from datetime import timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from vanguard.common import Rejected
from vanguard.pki import load_cert, now, validate_certificate, validate_crl, validate_fetched_crl


def test_ca_issue_is_idempotent_and_revoke_is_idempotent(lab):
    assert lab["ca"].issue("vm-client", lab["request"]["csr"]) == lab["issued"]
    lab["ca"].revoke(lab["issued"]["serial"])
    lab["ca"].revoke(lab["issued"]["serial"])
    crl = validate_crl(lab["admission"].root, lab["ca"].crl())
    assert crl.get_revoked_certificate_by_serial_number(int(lab["issued"]["serial"], 16))


@pytest.mark.parametrize(
    "case",
    ["expired", "future", "revoked", "wrong_issuer", "ca", "server_eku", "wrong_cn", "critical"],
)
def test_certificate_rejections(lab, case):
    root = lab["admission"].root
    root_key = serialization.load_pem_private_key(
        (lab["ca"].path / "private/root.key").read_bytes(), None
    )
    at = now()
    builder = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(
                        NameOID.COMMON_NAME, "wrong" if case == "wrong_cn" else "vm-client"
                    )
                ]
            )
        )
        .issuer_name(root.subject)
    )
    builder = (
        builder.public_key(lab["key"].public_key())
        .serial_number(9999)
        .not_valid_before(at + timedelta(hours=1) if case == "future" else at - timedelta(days=2))
        .not_valid_after(at - timedelta(days=1) if case == "expired" else at + timedelta(days=1))
    )
    builder = builder.add_extension(x509.BasicConstraints(ca=case == "ca", path_length=None), True)
    builder = builder.add_extension(
        x509.KeyUsage(True, False, False, False, False, False, False, False, False), True
    )
    builder = builder.add_extension(
        x509.ExtendedKeyUsage(
            [
                ExtendedKeyUsageOID.SERVER_AUTH
                if case == "server_eku"
                else ExtendedKeyUsageOID.CLIENT_AUTH
            ]
        ),
        False,
    )
    if case == "critical":
        builder = builder.add_extension(
            x509.UnrecognizedExtension(x509.ObjectIdentifier("1.2.3.4.5"), b"test"), True
        )
    cert = builder.sign(
        ec.generate_private_key(ec.SECP256R1()) if case == "wrong_issuer" else root_key,
        hashes.SHA256(),
    )
    crl_builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(root.subject)
        .last_update(at - timedelta(seconds=1))
        .next_update(at + timedelta(hours=1))
    )
    if case == "revoked":
        crl_builder = crl_builder.add_revoked_certificate(
            x509.RevokedCertificateBuilder().serial_number(9999).revocation_date(at).build()
        )
    crl = crl_builder.sign(root_key, hashes.SHA256())
    with pytest.raises(Rejected):
        validate_certificate(root, cert.public_bytes(serialization.Encoding.PEM), crl, "vm-client")


@pytest.mark.parametrize("case", ["stale", "future", "signature", "issuer"])
def test_crl_rejections(lab, case):
    root = lab["admission"].root
    root_key = serialization.load_pem_private_key(
        (lab["ca"].path / "private/root.key").read_bytes(), None
    )
    at = now()
    builder = x509.CertificateRevocationListBuilder().issuer_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Fake")])
        if case == "issuer"
        else root.subject
    )
    builder = builder.last_update(
        at + timedelta(seconds=10) if case == "future" else at - timedelta(hours=2)
    )
    builder = builder.next_update(
        at - timedelta(hours=1) if case == "stale" else at + timedelta(hours=1)
    )
    key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if case == "signature"
        else root_key
    )
    crl = builder.sign(key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM)
    with pytest.raises(Rejected) as failure:
        validate_crl(root, crl)
    assert failure.value.reason == {
        "stale": "crl_expired", "future": "crl_future",
        "signature": "crl_signature_invalid", "issuer": "crl_signature_invalid",
    }[case]


def test_wrong_csr_subject_rejected(lab):
    with pytest.raises(Rejected):
        lab["ca"].issue("different-device", lab["request"]["csr"])


@pytest.mark.parametrize("case", ["boundary", "far_future", "frozen", "expires", "signature"])
def test_fetched_crl_wait_never_accepts_outside_validity(lab, monkeypatch, case):
    from vanguard import pki

    root = lab["admission"].root
    key = serialization.load_pem_private_key(
        (lab["ca"].path / "private/root.key").read_bytes(), None
    )
    boundary = now().replace(microsecond=0) + timedelta(seconds=3)
    clock = [boundary - timedelta(seconds=2 if case == "far_future" else 0.05)]
    builder = (x509.CertificateRevocationListBuilder().issuer_name(root.subject)
               .last_update(boundary).next_update(boundary + timedelta(seconds=1)))
    crl = builder.sign(
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if case == "signature" else key, hashes.SHA256()
    ).public_bytes(serialization.Encoding.PEM)
    waits = []
    monkeypatch.setattr(pki, "now", lambda: clock[0])

    def sleep(seconds):
        waits.append(seconds)
        # At the start of any wait, strict validation MUST still reject this CRL.
        with pytest.raises(Rejected):
            validate_crl(root, crl)
        if case != "frozen":
            clock[0] += timedelta(seconds=2 if case == "expires" else seconds)

    monkeypatch.setattr(pki.time, "sleep", sleep)
    if case == "boundary":
        accepted = validate_fetched_crl(root, crl)
        assert accepted.last_update_utc <= clock[0] < accepted.next_update_utc
    else:
        with pytest.raises(Rejected) as failure:
            validate_fetched_crl(root, crl)
        assert failure.value.reason == {
            "far_future": "crl_future", "frozen": "crl_future",
            "expires": "crl_expired", "signature": "crl_signature_invalid",
        }[case]
    assert len(waits) == (0 if case in ("far_future", "signature") else 1)
    assert all(0 < wait <= 1 for wait in waits)


def test_root_is_ca(lab):
    cert = load_cert((lab["ca"].path / "root.crt").read_bytes())
    assert cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca


def test_openssl_tls_certificate_cannot_be_used_for_admission(lab, tmp_path):
    csr = tmp_path / "service.csr"
    csr.write_text(lab["request"]["csr"])
    output = tmp_path / "service.crt"
    lab["ca"].sign_tls(csr, "192.168.100.20", output)
    certificate = load_cert(output.read_bytes())
    certificate.verify_directly_issued_by(lab["admission"].root)
    eku = certificate.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    assert ExtendedKeyUsageOID.SERVER_AUTH in eku
    crl = validate_crl(lab["admission"].root, lab["ca"].crl())
    with pytest.raises(Rejected):
        validate_certificate(lab["admission"].root, output.read_bytes(), crl, "vm-client")
