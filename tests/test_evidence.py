"""Check interruption recovery without rebooting or connecting to a real VM."""

import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    # Script imports use the same module names as their command-line invocation.
    import evidence
    import verify_operations
    return evidence, verify_operations


def test_failed_report_write_preserves_previous_evidence(modules, tmp_path, monkeypatch):
    evidence, _ = modules
    path = tmp_path / "evidence.json"
    evidence.save_json(path, {"status": "RUNNING", "results": ["first"]})
    original = path.read_bytes()
    def fail(*args):
        raise OSError("simulated interrupted publication")
    monkeypatch.setattr(evidence.os, "replace", fail)
    with pytest.raises(OSError):
        evidence.save_json(path, {"status": "COMPLETE"})
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
    assert path.stat().st_mode & 0o777 == 0o600


def test_reboot_resume_preserves_evidence_and_skips_completed_nodes(modules, tmp_path):
    evidence, operations = modules
    path = tmp_path / "operations-reboot.json"
    previous = [{"test": "reboot_" + r, "status": "PASS", "detail": "earlier run"}
                for r in ("ca", "server", "client")]
    evidence.save_json(path, {"utc": "2026-10-08T08:03:11+00:00", "results": previous})
    instance = operations.Operations({}, tmp_path)
    rebooted = []
    boots = {}
    def ssh(role, command, **kwargs):
        if command == "sudo systemctl reboot":
            # Check that intention is on disk BEFORE rebooting a guest.
            current = json.loads(path.read_text())
            assert current["status"] == "RUNNING"
            assert current["current_step"] == "reboot_" + role
            rebooted.append(role)
            boots[role] = b"new"
        return boots.get(role, b"old")
    instance.ssh = ssh
    instance.ping = lambda: True
    instance.run("reboot", resume=True)
    report = json.loads(path.read_text())
    assert rebooted == ["admin", "attacker"]
    assert report["results"][:3] == previous
    assert report["status"] == "COMPLETE"
    with pytest.raises(FileExistsError):
        instance.run("reboot")


def test_interrupt_records_recovery_step(modules, tmp_path):
    _, operations = modules
    instance = operations.Operations({}, tmp_path)
    def interrupted():
        instance.record("firewall_matrix", "passed before interruption")
        raise KeyboardInterrupt()
    instance.matrix = interrupted
    with pytest.raises(KeyboardInterrupt):
        instance.run("matrix")
    report = json.loads((tmp_path / "operations-matrix.json").read_text())
    assert report["status"] == "INTERRUPTED"
    assert report["results"][0]["status"] == "PASS"
