import base64
import json
import time
from datetime import datetime, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .common import Rejected


def now():
    return datetime.now(timezone.utc)


def fingerprint(cert):
    return cert.fingerprint(hashes.SHA256()).hex()


def load_cert(pem):
    try:
        return x509.load_pem_x509_certificate(pem.encode() if isinstance(pem, str) else pem)
    except (ValueError, TypeError) as exc:
        raise Rejected("Invalid certificate") from exc


def check_csr(pem, name):
    try:
        csr = x509.load_pem_x509_csr(pem.encode())
        key = csr.public_key()
        names = csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if (
            not csr.is_signature_valid
            or len(names) != 1
            or names[0].value != name
            or not isinstance(key, ec.EllipticCurvePublicKey)
            or not isinstance(key.curve, ec.SECP256R1)
        ):
            raise ValueError()
        return csr
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise Rejected("CSR must be signed by a P-256 key with matching device CN") from exc


def validate_crl(root, pem, at=None):
    at = at or now()
    try:
        crl = x509.load_pem_x509_crl(pem)
        if crl.issuer != root.subject or not crl.is_signature_valid(root.public_key()):
            raise Rejected("CRL issuer or signature invalid", 403, "crl_signature_invalid")
        if crl.last_update_utc > at:
            raise Rejected(
                f"CRL lastUpdate {crl.last_update_utc.isoformat()} exceeds "
                f"validator time {at.isoformat()}", 403, "crl_future"
            )
        if crl.next_update_utc is None or crl.next_update_utc <= at:
            raise Rejected("CRL nextUpdate missing or elapsed", 403, "crl_expired")
        if not root.not_valid_before_utc <= at < root.not_valid_after_utc:
            raise Rejected("Root CA outside validity period", 403, "root_validity")
        root_usage = root.extensions.get_extension_for_class(x509.KeyUsage).value
        if not root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
            raise ValueError()
        if not root_usage.crl_sign or not root_usage.key_cert_sign:
            raise ValueError()
        return crl
    except (ValueError, TypeError, InvalidSignature, x509.ExtensionNotFound) as exc:
        raise Rejected("CRL or trust anchor is invalid/stale", 403, "crl_invalid") from exc


def validate_fetched_crl(root, pem):
    """Wait once for a signed CRL at a near-future second boundary, then revalidate."""
    try:
        return validate_crl(root, pem)
    except Rejected as exc:
        if exc.reason != "crl_future":
            raise
        # validate_crl has already checked issuer/signature. Never relax its clock
        # check or refetch here: a new CRL could move the boundary forward again.
        crl = x509.load_pem_x509_crl(pem)
        delay = (crl.last_update_utc - now()).total_seconds()
        if delay > 1:
            raise
        if delay > 0:
            time.sleep(delay)
        # Use the actual clock again; a backward step or early wake still rejects.
        return validate_crl(root, pem)


def validate_certificate(root, pem, crl, name=None, at=None):
    at = at or now()
    cert = load_cert(pem)
    try:
        cert.verify_directly_issued_by(root)
        if at < cert.not_valid_before_utc:
            raise Rejected("Certificate not yet valid", 403, "certificate_future")
        if cert.not_valid_after_utc <= at:
            raise Rejected("Certificate expired", 403, "certificate_expired")
        if cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
            raise ValueError()
        if not cert.extensions.get_extension_for_class(x509.KeyUsage).value.digital_signature:
            raise ValueError()
        eku = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
        if ExtendedKeyUsageOID.CLIENT_AUTH not in eku or ExtendedKeyUsageOID.SERVER_AUTH in eku:
            raise ValueError()
        key = cert.public_key()
        if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(
            key.curve, ec.SECP256R1
        ):
            raise ValueError()
        common_names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if len(common_names) != 1 or (name is not None and common_names[0].value != name):
            raise ValueError()
        if crl.get_revoked_certificate_by_serial_number(cert.serial_number) is not None:
            raise Rejected("Certificate revoked", 403, "certificate_revoked")
        supported = {
            x509.ExtensionOID.BASIC_CONSTRAINTS,
            x509.ExtensionOID.KEY_USAGE,
            x509.ExtensionOID.EXTENDED_KEY_USAGE,
        }
        if any(ext.critical and ext.oid not in supported for ext in cert.extensions):
            raise ValueError()
        return cert
    except (ValueError, TypeError, InvalidSignature, x509.ExtensionNotFound) as exc:
        raise Rejected("Certificate admission rejected", 403, "certificate_invalid") from exc


def proof_message(challenge_id, nonce, cert_hash, public_key, ip):
    return json.dumps(
        {
            "protocol": "vanguard-admission-v1",
            "challenge_id": challenge_id,
            "nonce": nonce,
            "certificate_sha256": cert_hash,
            "wg_public_key": public_key,
            "tunnel_ip": ip,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def verify_proof(cert, signature, message):
    try:
        cert.public_key().verify(
            base64.b64decode(signature, validate=True), message, ec.ECDSA(hashes.SHA256())
        )
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise Rejected("Private-key proof rejected", 403) from exc
