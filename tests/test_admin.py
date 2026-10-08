import io
import json
import time
from types import SimpleNamespace

import pyotp
import pytest
from conftest import LocalRemote
from werkzeug.security import generate_password_hash

from vanguard.admin import Dashboard, create_app
from vanguard.ca import create_app as ca_app
from vanguard.common import Rejected, database


@pytest.fixture
def dashboard(lab, tmp_path):
    authority = ca_app({"CA_DIR": lab["ca"].path, "TOKEN": "c" * 32})
    dash = Dashboard(tmp_path / "admin", LocalRemote(authority, "c" * 32), lab["management"])
    secret = pyotp.random_base32()
    with database(dash.db) as db:
        db.execute(
            "INSERT INTO users(username,password_hash,totp_secret) VALUES (?,?,?)",
            ("admin", generate_password_hash("test-password-long"), secret),
        )
    app = create_app({"DASHBOARD": dash, "SECRET_KEY": "x" * 32})
    app.config["TESTING"] = True
    return dash, app.test_client(), secret


def csrf(client):
    client.get("/login", base_url="https://localhost")
    with client.session_transaction() as state:
        return state["csrf"]


def login(client, secret, code=None):
    return client.post(
        "/login",
        base_url="https://localhost",
        data={
            "csrf": csrf(client),
            "username": "admin",
            "password": "test-password-long",
            "totp": code or pyotp.TOTP(secret).now(),
        },
    )


def test_requires_login_and_csrf(dashboard):
    _, client, _ = dashboard
    assert client.get("/", base_url="https://localhost").status_code == 302
    assert client.post("/devices", base_url="https://localhost").status_code == 403


def test_login_requires_totp_and_rejects_replay(dashboard, monkeypatch):
    _, client, secret = dashboard
    at = time.time()
    monkeypatch.setattr("vanguard.admin.time", SimpleNamespace(time=lambda: at))
    code = pyotp.TOTP(secret).at(at)
    response = client.post(
        "/login",
        base_url="https://localhost",
        data={
            "csrf": csrf(client),
            "username": "admin",
            "password": "test-password-long",
            "totp": "invalid",
        },
    )
    assert response.status_code == 401
    assert login(client, secret, code).status_code == 302
    assert client.get("/", base_url="https://localhost").status_code == 200
    assert login(client, secret, code).status_code == 401


def test_lockout_persists(dashboard):
    dash, _, secret = dashboard
    for _ in range(5):
        assert dash.login("admin", "wrong", "wrong", "127.0.0.1") is None
    assert dash.login("admin", "test-password-long", pyotp.TOTP(secret).now(), "127.0.0.1") is None


def test_dashboard_enrollment_revocation_and_logout(lab, dashboard):
    dash, client, secret = dashboard
    assert login(client, secret).status_code == 302
    with client.session_transaction() as state:
        token = state["csrf"]
    response = client.post(
        "/devices",
        base_url="https://localhost",
        data={
            "csrf": token,
            "enrollment": (io.BytesIO(json.dumps(lab["request"]).encode()), "request.json"),
        },
    )
    assert response.status_code == 302
    assert dash.device("vm-client")["status"] == "registered"
    assert lab["wg"].additions == []
    assert (
        client.get("/devices/vm-client/certificate", base_url="https://localhost").status_code
        == 200
    )
    response = client.post(
        "/devices/vm-client/revoke", base_url="https://localhost", data={"csrf": token}
    )
    assert response.status_code == 302
    assert dash.device("vm-client")["status"] == "revoked"
    client.post("/logout", base_url="https://localhost", data={"csrf": token})
    assert client.get("/", base_url="https://localhost").status_code == 302


def test_partial_registration_retries_without_second_certificate(lab, dashboard):
    dash, _, _ = dashboard
    original = dash.server

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected("Offline", 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.register(lab["request"])
    row = dash.device("vm-client")
    assert row["status"] == "pending_registry"
    assert not lab["wg"].active
    dash.server = original
    dash.retry("vm-client")
    assert dash.device("vm-client")["serial"] == row["serial"]
    assert dash.device("vm-client")["status"] == "registered"


def test_ca_revocation_still_attempted_when_server_offline(lab, dashboard):
    dash, _, _ = dashboard
    dash.register(lab["request"])

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected("Offline", 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.revoke("vm-client")
    assert dash.device("vm-client")["status"] == "revoking"
    from vanguard.pki import validate_crl

    crl = validate_crl(lab["admission"].root, lab["ca"].crl())
    assert crl.get_revoked_certificate_by_serial_number(int(lab["issued"]["serial"], 16))
