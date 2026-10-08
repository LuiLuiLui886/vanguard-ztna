import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import proof, random_wg, register
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from vanguard.client import admit, initialize
from vanguard.common import Rejected, database


def test_registration_never_adds_peer_and_client_admission_does(lab):
    body = register(lab)
    assert lab["wg"].active == {} and lab["wg"].additions == []
    lab["management"].call("POST", "/api/devices", body)
    assert lab["wg"].additions == []
    result = admit(lab["directory"], lab["remote"])
    assert result["decision"] == "ACCEPT"
    assert lab["wg"].active == {body["wg_public_key"]: "10.8.0.2"}


def test_no_management_token(lab):
    for method, path, data in [
        ("GET", "/api/devices", None),
        ("GET", "/api/audit", None),
        ("POST", "/api/devices", {}),
        ("POST", "/api/devices/vm-client/disable", {}),
    ]:
        with pytest.raises(Rejected) as failure:
            lab["remote"].call(method, path, data)
        assert failure.value.status == 401


def test_unknown_device_cannot_challenge(lab):
    with pytest.raises(Rejected):
        proof(lab)
    assert not lab["wg"].active


def test_proof_is_one_time_even_when_concurrent(lab):
    register(lab)
    body = proof(lab)

    def verify():
        try:
            return lab["admission"].verify(body)["decision"]
        except Rejected:
            return "REJECT"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: verify(), range(2)))
    assert sorted(outcomes) == ["ACCEPT", "REJECT"]
    assert len(lab["wg"].additions) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("wg_public_key", "wrong"),
        ("signature", "invalid-base64"),
        ("certificate", "not a certificate"),
    ],
)
def test_tampering_consumes_challenge_without_adding_peer(lab, field, value):
    register(lab)
    body = proof(lab)
    original = dict(body)
    body[field] = value
    with pytest.raises(Rejected):
        lab["admission"].verify(body)
    with pytest.raises(Rejected):
        lab["admission"].verify(original)
    assert lab["wg"].additions == []


def test_wrong_private_key(lab):
    register(lab)
    body = proof(lab)
    body["signature"] = base64.b64encode(
        ec.generate_private_key(ec.SECP256R1()).sign(b"unrelated", ec.ECDSA(hashes.SHA256()))
    ).decode()
    with pytest.raises(Rejected, match="proof"):
        lab["admission"].verify(body)
    assert not lab["wg"].active


def test_expired_challenge(lab):
    register(lab)
    body = proof(lab)
    with database(lab["admission"].db) as db:
        db.execute("UPDATE challenges SET expires=?", (time.time() - 1,))
    with pytest.raises(Rejected, match="expired"):
        lab["admission"].verify(body)


def test_revocation_between_challenge_and_verify(lab):
    register(lab)
    body = proof(lab)
    lab["ca"].revoke(lab["issued"]["serial"])
    with pytest.raises(Rejected):
        lab["admission"].verify(body)
    assert not lab["wg"].active


def test_revocation_removes_live_peer(lab):
    register(lab)
    lab["admission"].verify(proof(lab))
    lab["ca"].revoke(lab["issued"]["serial"])
    lab["admission"].reconcile()
    assert not lab["wg"].active
    with database(lab["admission"].db) as db:
        row = db.execute("SELECT * FROM audit WHERE event='peer_removed'").fetchone()
    assert row["device_id"] == "vm-client"
    assert json.loads(row["detail"])["reason"] == "certificate_revoked"


@pytest.mark.parametrize("reason", ["expiry", "outage", "unknown", "restart"])
def test_reconciliation_removes_ineligible_peers(lab, reason):
    register(lab)
    lab["admission"].verify(proof(lab))
    if reason == "expiry":
        with database(lab["admission"].db) as db:
            db.execute("UPDATE devices SET lease_until=0")
    elif reason == "outage":

        def unavailable():
            raise Rejected("CA offline", 503)

        lab["admission"].fetch_crl = unavailable
    elif reason == "unknown":
        lab["wg"].active[random_wg()] = "10.8.0.99"
    lab["admission"].reconcile(startup=reason == "restart")
    assert len(lab["wg"].active) == (1 if reason == "unknown" else 0)
    with database(lab["admission"].db) as db:
        row = db.execute("SELECT * FROM audit WHERE event='peer_removed'").fetchone()
    detail = json.loads(row["detail"])
    assert detail["reason"] == {
        "expiry": "lease_expired", "outage": "crl_unavailable",
        "unknown": "unknown_peer", "restart": "startup_reset",
    }[reason]
    assert row["device_id"] == (None if reason == "unknown" else "vm-client")
    if reason == "outage":
        assert detail["crl_error"] == "CA offline"


def test_future_crl_removes_peer_with_precise_diagnosis(lab):
    register(lab)
    lab["admission"].verify(proof(lab))

    def future_crl():
        raise Rejected("CRL lastUpdate exceeds validator time", 403, "crl_future")

    lab["admission"].fetch_crl = future_crl
    lab["admission"].reconcile()
    assert not lab["wg"].active
    with database(lab["admission"].db) as db:
        row = db.execute("SELECT * FROM audit WHERE event='peer_removed'").fetchone()
        assert db.execute("SELECT lease_until FROM devices").fetchone()[0] == 0
    assert json.loads(row["detail"])["reason"] == "crl_future"
    assert row["device_id"] == "vm-client"


def test_challenge_expiring_during_crl_fetch_cannot_add_peer(lab, monkeypatch):
    from vanguard import server

    register(lab)
    body = proof(lab)
    crl = lab["ca"].crl()
    after_expiry = server.time.time() + 61

    def slow_fetch():
        monkeypatch.setattr(server.time, "time", lambda: after_expiry)
        return crl

    lab["admission"].fetch_crl = slow_fetch
    with pytest.raises(Rejected, match="Challenge expired during verification"):
        lab["admission"].verify(body)
    assert not lab["wg"].active
    assert not lab["wg"].additions


def test_disable_is_terminal_and_idempotent(lab):
    body = register(lab)
    lab["admission"].verify(proof(lab))
    lab["admission"].disable("vm-client")
    lab["admission"].disable("vm-client")
    assert not lab["wg"].active
    with pytest.raises(Rejected):
        lab["admission"].register(body)
    with pytest.raises(Rejected):
        proof(lab)


def test_identity_cannot_be_rebound(lab):
    body = register(lab)
    body["wg_public_key"] = random_wg()
    with pytest.raises(Rejected):
        lab["admission"].register(body)
    assert not lab["wg"].active


def test_rate_limit_and_challenge_capacity(lab):
    register(lab)
    for _ in range(5):
        proof(lab)
    with pytest.raises(Rejected) as exc:
        proof(lab)
    assert exc.value.status == 429
    for _ in range(30):
        lab["admission"].throttle("another-client")
    with pytest.raises(Rejected) as exc:
        lab["admission"].throttle("another-client")
    assert exc.value.status == 429


def test_tunnel_address_reusable_only_after_old_identity_disabled(lab, tmp_path):
    register(lab)
    directory = tmp_path / "replacement"
    initialize(directory, "replacement")
    body = json.loads((directory / "request.json").read_text())
    issued = lab["ca"].issue(body["device_id"], body.pop("csr"))
    body["certificate"] = issued["certificate"]
    with pytest.raises(Rejected):
        lab["admission"].register(body)
    lab["admission"].disable("vm-client")
    lab["admission"].register(body)
    assert lab["wg"].additions == []


def test_wg_failure_never_records_lease(lab, monkeypatch):
    register(lab)
    body = proof(lab)

    def fail(*_):
        raise Rejected("WireGuard unavailable", 503)

    monkeypatch.setattr(lab["wg"], "add", fail)
    with pytest.raises(Rejected):
        lab["admission"].verify(body)
    with database(lab["admission"].db) as db:
        assert db.execute("SELECT lease_until FROM devices").fetchone()[0] == 0
    assert not lab["wg"].active
