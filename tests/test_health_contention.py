import fcntl
import hashlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from vanguard import health


def snapshot(path):
    return {str(p.relative_to(path)): (p.stat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in path.rglob('*') if p.is_file()}


@pytest.mark.parametrize('pending', [False, True])
def test_short_ca_writer_contention_waits_then_checks_without_mutation(lab, monkeypatch, pending):
    path = lab['ca'].path
    monkeypatch.setenv('VANGUARD_CA_DIR', str(path))
    if pending:
        transaction = path / '.transaction'
        transaction.mkdir(exist_ok=True)
        (transaction / 'commit.json').write_text('{"must_not_recover": true}')
    before = snapshot(path)
    with (path / 'ca.lock').open('rb') as writer, ThreadPoolExecutor(1) as pool:
        fcntl.flock(writer, fcntl.LOCK_EX)
        result = pool.submit(health.probe, 'ca')
        try:
            time.sleep(0.2)
            assert not result.done(), 'Probe returned before a short writer released its lock'
        finally:
            fcntl.flock(writer, fcntl.LOCK_UN)
        expected = 'not_ready' if pending else 'ready'
        assert result.result(timeout=5)['status'] == expected
    assert snapshot(path) == before


def test_ca_writer_beyond_budget_is_unknown_and_does_not_change_state(lab, monkeypatch):
    path = lab['ca'].path
    monkeypatch.setenv('VANGUARD_CA_DIR', str(path))
    before = snapshot(path)
    with (path / 'ca.lock').open('rb') as writer:
        fcntl.flock(writer, fcntl.LOCK_EX)
        started = time.monotonic()
        result = health.probe('ca')
        elapsed = time.monotonic() - started
    assert result == {'status': 'not_ready', 'checks': {'ca_state': 'unknown'}}
    assert 3 <= elapsed < 5.5
    assert snapshot(path) == before


def test_corrupt_state_after_writer_release_is_never_ready(lab, monkeypatch):
    path = lab['ca'].path
    monkeypatch.setenv('VANGUARD_CA_DIR', str(path))
    with (path / 'ca.lock').open('rb') as writer, ThreadPoolExecutor(1) as pool:
        fcntl.flock(writer, fcntl.LOCK_EX)
        result = pool.submit(health.probe, 'ca')
        try:
            time.sleep(0.2)
            (path / 'serial').write_text('')
        finally:
            fcntl.flock(writer, fcntl.LOCK_UN)
        assert result.result(timeout=5)['status'] == 'not_ready'
    assert (path / 'serial').read_bytes() == b''


def test_admin_dependencies_overlap_and_failure_remains_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv('VANGUARD_ADMIN_DIR', str(tmp_path))
    monkeypatch.setattr(health, 'database_ready', lambda path: True)
    barrier = threading.Barrier(2)
    calls = []

    def dependency(url, trust, **kwargs):
        calls.append(url)
        # Sequential probes cannot both reach this barrier.
        barrier.wait(timeout=2)
        if ':8080' in url:
            raise OSError('Synthetic dependency unavailable')
        return True

    monkeypatch.setattr(health, 'dependency_ready', dependency)
    result = health.probe('admin')
    assert len(calls) == 2
    assert result == {'status': 'not_ready',
                      'checks': {'database': 'ready', 'ca': 'unknown', 'server': 'ready'}}


@pytest.mark.parametrize('role', ['ca', 'server'])
def test_dependency_read_timeout_allows_its_nested_probe(role, monkeypatch):
    captured = {}

    def get(url, **kwargs):
        captured.update(kwargs)
        class Response:
            status_code = 200

            def json(self):
                return {'status': 'ready'}
        return Response()

    monkeypatch.setattr(health.requests, 'get', get)
    assert health.dependency_ready('https://example.invalid', '/trusted/root.crt', role=role)
    assert captured['verify'] == '/trusted/root.crt'
    assert captured['allow_redirects'] is False
    connect, read = captured['timeout']
    assert connect == 0.5
    assert 3.5 < read < 6
    assert read == (4.25 if role == 'ca' else 5)


def test_actual_hung_probe_is_terminated_by_outer_deadline(tmp_path, monkeypatch):
    wrapper = tmp_path / 'hung-python'
    wrapper.write_text(f'#!{sys.executable}\nimport time\ntime.sleep(60)\n')
    wrapper.chmod(0o700)
    monkeypatch.setattr(health.sys, 'executable', str(wrapper))
    started = time.monotonic()
    assert health.bounded_readiness('ca') == {
        'status': 'not_ready', 'checks': {'probe': 'unknown'}}
    assert 5.5 < time.monotonic() - started < 9
