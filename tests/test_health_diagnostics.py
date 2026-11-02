import fcntl
import json
import socket
import subprocess
import sys
import time

import pytest
import requests

from vanguard import health


@pytest.mark.parametrize('error,reason', [
    (requests.exceptions.ConnectTimeout, 'connect_timeout'),
    (requests.exceptions.ReadTimeout, 'read_timeout'),
    (requests.exceptions.SSLError, 'tls_error'),
    (requests.exceptions.ConnectionError, 'connection_error'),
    (ValueError, 'invalid_data'),
    (RuntimeError, 'check_error'),
])
def test_diagnostics_separate_failures_without_disclosing_exception(tmp_path, monkeypatch,
                                                                 error, reason):
    secret = 'private-sentinel-password-token-and-key'
    monkeypatch.setenv('VANGUARD_ADMIN_DIR', str(tmp_path))
    monkeypatch.setattr(health, 'database_ready', lambda path: True)

    def fail(url, trust, **kwargs):
        raise error('https://user:' + secret + '@example.invalid/?token=' + secret)

    monkeypatch.setattr(health, 'dependency_ready', fail)
    default = health.probe('admin')
    diagnostic = health.probe('admin', diagnostics=True)
    assert default == {'status': 'not_ready',
                       'checks': {'database': 'ready', 'ca': 'unknown', 'server': 'unknown'}}
    assert {k: v for k, v in diagnostic.items() if k != 'diagnostics'} == default
    assert diagnostic['diagnostics']['ca']['reason'] == reason
    assert diagnostic['diagnostics']['server']['reason'] == reason
    assert diagnostic['diagnostics']['ca']['elapsed_ms'] >= 0
    assert secret not in json.dumps(diagnostic)
    assert 'example.invalid' not in json.dumps(diagnostic)


def test_real_refused_connection_is_diagnosed_without_url(tmp_path, monkeypatch):
    monkeypatch.setenv('VANGUARD_ADMIN_DIR', str(tmp_path))
    monkeypatch.setattr(health, 'database_ready', lambda path: True)
    # Bound but not listening: keep the port reserved and refuse TCP connections.
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))
        url = f'https://127.0.0.1:{reserved.getsockname()[1]}'
        monkeypatch.setenv('VANGUARD_CA_URL', url)
        monkeypatch.setenv('VANGUARD_SERVER_URL', url)
        monkeypatch.setenv('VANGUARD_ROOT_CERT', requests.certs.where())
        monkeypatch.setenv('NO_PROXY', '127.0.0.1')
        result = health.probe('admin', diagnostics=True)
    assert result['status'] == 'not_ready'
    assert result['diagnostics']['ca']['reason'] == 'connection_error'
    assert result['diagnostics']['server']['reason'] == 'connection_error'
    assert url not in json.dumps(result)


def test_ca_lock_diagnostic_retains_state_and_does_not_recover(lab, monkeypatch):
    path = lab['ca'].path
    monkeypatch.setenv('VANGUARD_CA_DIR', str(path))
    before = {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}
    with (path / 'ca.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = health.probe('ca', diagnostics=True)
    assert result['checks'] == {'ca_state': 'unknown'}
    assert result['diagnostics']['ca_state']['reason'] == 'lock_busy'
    assert 3000 <= result['diagnostics']['ca_state']['elapsed_ms'] < 5500
    assert {str(p.relative_to(path)): p.read_bytes()
            for p in path.rglob('*') if p.is_file()} == before
    healthy = health.probe('ca', diagnostics=True)
    assert healthy['status'] == 'ready'
    assert healthy['diagnostics']['ca_state']['reason'] == 'ok'


def test_diagnostic_subprocess_timeout_has_safe_reason(tmp_path, monkeypatch):
    wrapper = tmp_path / 'hung-python'
    wrapper.write_text(f'#!{sys.executable}\nimport time\ntime.sleep(60)\n')
    wrapper.chmod(0o700)
    monkeypatch.setattr(health.sys, 'executable', str(wrapper))
    started = time.monotonic()
    result = health.bounded_readiness('ca', diagnostics=True)
    assert result == {'status': 'not_ready', 'checks': {'probe': 'unknown'},
                      'diagnostics': {'probe': {'reason': 'process_timeout'}}}
    assert 5.5 < time.monotonic() - started < 9
    assert str(wrapper) not in json.dumps(result)


def test_diagnostic_cli_is_bounded_and_does_not_create_missing_ca(tmp_path, monkeypatch):
    missing = tmp_path / 'absent-ca'
    monkeypatch.setenv('VANGUARD_CA_DIR', str(missing))
    result = subprocess.run([sys.executable, '-m', 'vanguard.health', 'ca', '--diagnose'],
                            capture_output=True, text=True, check=True, timeout=9)
    body = json.loads(result.stdout)
    assert body['status'] == 'not_ready'
    assert body['diagnostics']['ca_state']['reason'] == 'file_missing'
    assert not missing.exists()
    assert str(missing) not in result.stdout
    assert result.stderr == ''
