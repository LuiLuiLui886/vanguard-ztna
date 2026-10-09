import ipaddress
import threading
from contextlib import contextmanager
from datetime import timedelta

import pytest
from conftest import FakeWireGuard
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from requests import certs
from werkzeug.serving import make_server

from vanguard.admin import Dashboard
from vanguard.ca import create_app as create_ca
from vanguard.client import admit, login_employee
from vanguard.common import Rejected, Remote
from vanguard.pki import now
from vanguard.server import Admission
from vanguard.server import create_app as create_server


@contextmanager
def https(app, certificate, key):
    server = make_server(
        "127.0.0.1", 0, app, threaded=True, ssl_context=(str(certificate), str(key))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_real_https_ca_admin_server_client_flow(lab, tmp_path):
    root = lab["admission"].root
    root_key = serialization.load_pem_private_key(
        (lab["ca"].path / "private/root.key").read_bytes(), None
    )
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test TLS")]))
        .issuer_name(root.subject)
        .public_key(key.public_key())
        .serial_number(8888)
        .not_valid_before(now() - timedelta(minutes=1))
        .not_valid_after(now() + timedelta(hours=1))
        .add_extension(x509.BasicConstraints(False, None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False
        )
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
        .sign(root_key, hashes.SHA256())
    )
    certificate, key_path = tmp_path / "tls.crt", tmp_path / "tls.key"
    certificate.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    root_path = lab["ca"].path / "root.crt"
    ca = create_ca({"CA_DIR": lab["ca"].path, "TOKEN": "c" * 32})
    with https(ca, certificate, key_path) as ca_url:
        ca_remote = Remote(ca_url, root_path, "c" * 32)
        wg = FakeWireGuard()
        admission = Admission(
            tmp_path / "https-server",
            root_path.read_bytes(),
            lambda: ca_remote.call("GET", "/api/ca/crl", raw=True),
            wg,
        )
        app = create_server({"ADMISSION": admission, "TOKEN": "s" * 32, "TESTING": True})
        admission.employees.create('employee-test', 'employee-test-password')
        with https(app, certificate, key_path) as server_url:
            dashboard = Dashboard(
                tmp_path / "https-admin", ca_remote, Remote(server_url, root_path, "s" * 32)
            )
            dashboard.register(lab["request"])
            assert wg.active == {}
            login_employee(lab['directory'], Remote(server_url, root_path),
                           'employee-test', 'employee-test-password')
            result = admit(lab["directory"], Remote(server_url, root_path))
            assert result["decision"] == "ACCEPT" and len(wg.active) == 1
            dashboard.revoke("vm-client")
            assert not wg.active
            with pytest.raises(Rejected):
                admit(lab["directory"], Remote(server_url, root_path))
            with pytest.raises(Rejected):
                Remote(server_url, certs.where()).call("GET", "/healthz")


def test_plain_http_configuration_rejected():
    with pytest.raises(RuntimeError, match="HTTPS"):
        Remote("http://192.168.100.20:8081", "root.crt")
