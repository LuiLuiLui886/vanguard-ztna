import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519

from vanguard.ca import Authority
from vanguard.client import initialize
from vanguard.common import Rejected
from vanguard.pki import fingerprint, load_cert, proof_message
from vanguard.server import Admission, create_app


class FakeWireGuard:
    def __init__(self):
        self.active = {}
        self.additions = []

    def peers(self):
        return set(self.active)

    def add(self, key, ip):
        self.active[key] = ip
        self.additions.append((key, ip))

    def remove(self, key):
        self.active.pop(key, None)


class LocalRemote:
    def __init__(self, app, token=None):
        self.client = app.test_client()
        self.token = token

    def call(self, method, path, data=None, raw=False):
        headers = {"Authorization": "Bearer " + self.token} if self.token else {}
        result = self.client.open(path, method=method, json=data, headers=headers)
        if result.status_code >= 300:
            error = Rejected(result.json["error"], result.status_code)
            error.upstream_status = result.status_code
            raise error
        return result.data if raw else result.json


@pytest.fixture
def lab(tmp_path):
    ca = Authority(tmp_path / "ca")
    ca.initialize()
    client_dir = tmp_path / "client"
    initialize(client_dir, "vm-client")
    request = json.loads((client_dir / "request.json").read_text())
    issued = ca.issue(request["device_id"], request["csr"])
    (client_dir / "device.crt").write_text(issued["certificate"])
    key = serialization.load_pem_private_key((client_dir / "identity.key").read_bytes(), None)
    wg = FakeWireGuard()
    admission = Admission(tmp_path / "server", (ca.path / "root.crt").read_bytes(), ca.crl, wg)
    app = create_app({"ADMISSION": admission, "TOKEN": "s" * 32, "TESTING": True})
    return {
        "ca": ca,
        "directory": client_dir,
        "request": request,
        "issued": issued,
        "key": key,
        "wg": wg,
        "admission": admission,
        "app": app,
        "remote": LocalRemote(app),
        "management": LocalRemote(app, "s" * 32),
    }


def register(lab):
    body = {
        "device_id": "vm-client",
        "certificate": lab["issued"]["certificate"],
        "wg_public_key": lab["request"]["wg_public_key"],
        "tunnel_ip": "10.8.0.2",
    }
    lab["management"].call("POST", "/api/devices", body)
    return body


def proof(lab):
    pem, public = lab["issued"]["certificate"], lab["request"]["wg_public_key"]
    challenge = lab["remote"].call(
        "POST", "/api/challenge", {"certificate": pem, "wg_public_key": public}
    )
    message = proof_message(
        challenge["challenge_id"],
        challenge["nonce"],
        fingerprint(load_cert(pem)),
        public,
        "10.8.0.2",
    )
    signature = lab["key"].sign(message, ec.ECDSA(hashes.SHA256()))
    return {
        "challenge_id": challenge["challenge_id"],
        "certificate": pem,
        "wg_public_key": public,
        "signature": base64.b64encode(signature).decode(),
    }


def random_wg():
    return base64.b64encode(
        x25519.X25519PrivateKey.generate()
        .public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
