import base64
import json
import os
import time
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from vanguard import client
from vanguard.common import Rejected
from vanguard.windows import WindowsTunnel

SERVER_KEY = base64.b64encode(b's' * 32).decode()


@pytest.mark.skipif(os.name == 'nt', reason='POSIX lock path protection')
@pytest.mark.parametrize('link_type', ['symlink', 'hardlink'])
def test_local_lock_rejects_link_without_modifying_target(tmp_path, link_type):
    target = tmp_path / 'unrelated'
    target.write_text('sentinel')
    target.chmod(0o644)
    path = tmp_path / 'lock'
    if link_type == 'symlink':
        path.symlink_to(target)
    else:
        os.link(target, path)
    with pytest.raises(Rejected):
        with client.local_lock(path):
            pytest.fail('Unsafe lock was accepted')
    assert target.read_text() == 'sentinel'
    assert target.stat().st_mode & 0o777 == 0o644


def test_local_lock_excludes_competing_operation_and_releases(tmp_path):
    path = tmp_path / 'lock'
    with client.local_lock(path):
        with pytest.raises(Rejected, match='Another client operation'):
            with client.local_lock(path):
                pytest.fail('Competing operation entered the lock')
    with client.local_lock(path):
        pass


class RecordingTunnel:
    name = 'vanguard-client'

    def __init__(self, fail_up=False, fail_down=False):
        self.events = []
        self.fail_up, self.fail_down = fail_up, fail_down

    def preflight(self):
        self.events.append('preflight')

    def up(self, path):
        self.events.append(('up', path.read_text()))
        if self.fail_up:
            raise Rejected('partial installation failed')

    def down(self, path):
        self.events.append('down')
        if self.fail_down:
            raise Rejected('cleanup failed')


def setup_client(tmp_path):
    directory = tmp_path / 'identity'
    client.initialize(directory, 'vm-client-windows', '10.8.0.4')
    return directory


def accepted(address='10.8.0.4'):
    return {'decision': 'ACCEPT', 'tunnel_ip': address, 'lease_until': time.time() + 60}


def test_separate_client_keys_and_addresses(tmp_path):
    ubuntu, windows = tmp_path / 'ubuntu', tmp_path / 'windows'
    client.initialize(ubuntu, 'vm-client')
    client.initialize(windows, 'vm-client-windows', '10.8.0.4')
    assert json.loads((ubuntu / 'request.json').read_text())['tunnel_ip'] == '10.8.0.2'
    assert json.loads((windows / 'request.json').read_text())['tunnel_ip'] == '10.8.0.4'
    for name in ('wg.key', 'identity.key'):
        assert (ubuntu / name).read_bytes() != (windows / name).read_bytes()
    before = (windows / 'identity.key').read_bytes()
    with pytest.raises(Rejected, match='empty'):
        client.initialize(windows, 'vm-client-windows', '10.8.0.4')
    assert (windows / 'identity.key').read_bytes() == before


@pytest.mark.parametrize('address', ['10.8.0.1', '10.8.0.0', '10.8.0.255', '192.168.100.60', 'bad'])
def test_init_rejects_invalid_address_before_writing(tmp_path, address):
    with pytest.raises(Rejected):
        client.initialize(tmp_path / 'identity', 'windows-client', address)
    assert not (tmp_path / 'identity').exists()


def test_session_replace_handles_repeated_login(tmp_path):
    class Remote:
        def call(self, method, endpoint, data):
            return {'username': 'test-user', 'session_token': data['password'],
                    'expires_at': time.time() + 60}
    directory = tmp_path / 'identity'
    client.login_employee(directory, Remote(), 'test-user', 'first-test-token')
    client.login_employee(directory, Remote(), 'test-user', 'second-test-token')
    assert json.loads((directory / 'employee-session.json').read_text())['session_token'] == 'second-test-token'
    assert {p.name for p in directory.iterdir()} == {'employee-session.json', '.session.lock'}


@pytest.mark.parametrize('response', [None, {}, {'decision': 'DENY'}, accepted('10.8.0.2'),
                                     {**accepted(), 'lease_until': 0},
                                     {**accepted(), 'lease_until': float('nan')}])
def test_bad_admission_never_starts_tunnel(tmp_path, monkeypatch, response):
    directory, backend = setup_client(tmp_path), RecordingTunnel()
    monkeypatch.setattr(client, 'admit', lambda *args: response)
    with pytest.raises(Rejected):
        client.connect(directory, None, SERVER_KEY, backend)
    assert backend.events == ['preflight']
    assert not (directory / 'vanguard-client.conf').exists()


@pytest.mark.parametrize('failure', ['revoked', 'wrong-address', 'partial-start', 'cleanup'])
def test_renewal_and_partial_install_cleanup(tmp_path, monkeypatch, failure):
    directory = setup_client(tmp_path)
    backend = RecordingTunnel(fail_up=failure == 'partial-start', fail_down=failure == 'cleanup')
    calls = []

    def admission(*args):
        calls.append('admit')
        if len(calls) == 1:
            return accepted()
        if failure == 'wrong-address':
            return accepted('10.8.0.2')
        raise Rejected('revoked')

    monkeypatch.setattr(client, 'admit', admission)
    monkeypatch.setattr(client.time, 'sleep', lambda *args: None)
    with pytest.raises(Rejected):
        client.connect(directory, None, SERVER_KEY, backend)
    assert backend.events[1][0] == 'up'
    config = backend.events[1][1]
    assert 'Address = 10.8.0.4/32' in config and 'AllowedIPs = 10.8.0.1/32' in config
    assert backend.events[-1] == 'down'
    assert (directory / 'vanguard-client.conf').exists() == (failure == 'cleanup')


def test_existing_config_refuses_admission(tmp_path, monkeypatch):
    directory = setup_client(tmp_path)
    path = directory / 'vanguard-client.conf'
    path.write_text('existing configuration')
    monkeypatch.setattr(client, 'admit', lambda *args: pytest.fail('must not admit'))
    with pytest.raises(Rejected, match='exists'):
        client.connect(directory, None, SERVER_KEY, RecordingTunnel())
    assert path.read_text() == 'existing configuration'


def test_windows_tunnel_uses_demand_start_and_native_cleanup(tmp_path, monkeypatch):
    from vanguard import windows
    calls = []
    monkeypatch.setattr(windows, 'run', lambda args: calls.append(args))
    monkeypatch.setattr(windows.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1060))
    backend = WindowsTunnel()
    config = tmp_path / 'vanguard-client.conf'
    backend.up(config)
    backend.down(config)
    assert calls[0][1:] == ['/installtunnelservice', str(config)]
    assert calls[1] == ['sc.exe', 'config', 'WireGuardTunnel$vanguard-client', 'start=', 'demand']
    assert calls[2][1:] == ['/uninstalltunnelservice', 'vanguard-client']


@pytest.mark.skipif(os.name != 'nt', reason='Requires real Windows ACL APIs')
def test_native_windows_private_acl(tmp_path):
    import win32security
    directory = setup_client(tmp_path)
    for path in (directory, directory / 'identity.key', directory / 'wg.key'):
        sd = win32security.GetNamedSecurityInfo(str(path), win32security.SE_FILE_OBJECT,
                                               win32security.DACL_SECURITY_INFORMATION)
        acl = sd.GetSecurityDescriptorDacl()
        assert acl is not None and acl.GetAceCount() == 2
        sids = {win32security.ConvertSidToStringSid(acl.GetAce(i)[2])
                for i in range(acl.GetAceCount())}
        assert sids == {'S-1-5-18', 'S-1-5-32-544'}


def test_windows_cleanup_waits_for_service_deletion(tmp_path, monkeypatch):
    from vanguard import windows
    results = iter([0, 1072, 1060])
    waits = []
    monkeypatch.setattr(windows, 'run', lambda args: None)
    monkeypatch.setattr(windows.subprocess, 'run',
                        lambda *a, **k: SimpleNamespace(returncode=next(results)))
    monkeypatch.setattr(windows.time, 'sleep', waits.append)
    backend = WindowsTunnel()
    backend.owns_service = True  # successful install by this process
    backend.down(tmp_path / 'vanguard-client.conf')
    assert len(waits) == 2


@pytest.mark.parametrize('result', [0, 5])
def test_windows_cleanup_failure_preserves_config(tmp_path, monkeypatch, result):
    from vanguard import windows
    directory = setup_client(tmp_path)
    backend = WindowsTunnel()
    backend.owns_service = True  # successful install by this process
    monkeypatch.setattr(backend, 'lock', nullcontext)
    monkeypatch.setattr(backend, 'preflight', lambda: None)
    monkeypatch.setattr(backend, 'up', lambda config: None)
    monkeypatch.setattr(client, 'admit', lambda *a: accepted())
    def stop(*args):
        raise KeyboardInterrupt()
    monkeypatch.setattr(client.time, 'sleep', stop)
    monkeypatch.setattr(windows, 'run', lambda args: None)
    monkeypatch.setattr(windows.subprocess, 'run',
                        lambda *a, **k: SimpleNamespace(returncode=result))
    ticks = iter([0, 16])
    monkeypatch.setattr(windows.time, 'monotonic', lambda: next(ticks))
    with pytest.raises(Rejected, match='removal'):
        client.connect(directory, None, SERVER_KEY, backend)
    assert (directory / 'vanguard-client.conf').exists()


def test_linux_refuses_foreign_interface_and_preserves_failed_start(tmp_path, monkeypatch):
    backend = client.LinuxTunnel()
    monkeypatch.setattr(backend, 'links', lambda: [{'ifname': 'wg0', 'ifalias': 'other-owner'}])
    with pytest.raises(Rejected, match='ownership'):
        backend.preflight()
    with pytest.raises(Rejected, match='ownership'):
        backend.down(tmp_path / 'wg0.conf')


def test_repeated_renewal_then_failure_cleans_owned_tunnel(tmp_path, monkeypatch):
    directory, backend = setup_client(tmp_path), RecordingTunnel()
    attempts = []
    def renew(*args):
        attempts.append(1)
        if len(attempts) == 6:
            raise Rejected('CA unavailable')
        return accepted()
    monkeypatch.setattr(client, 'admit', renew)
    monkeypatch.setattr(client.time, 'sleep', lambda _: None)
    with pytest.raises(Rejected, match='CA unavailable'):
        client.connect(directory, None, SERVER_KEY, backend)
    assert len(attempts) == 6
    assert backend.events[-1] == 'down'
    assert not (directory / 'vanguard-client.conf').exists()


def test_logout_unreachable_keeps_local_token_for_retry(tmp_path):
    directory = setup_client(tmp_path)
    saved = directory / 'employee-session.json'
    saved.write_text(json.dumps({'session_token': 'test-token-' * 4}))
    class Unavailable:
        def call(self, *args):
            raise Rejected('TLS unavailable', 503)
    with pytest.raises(Rejected, match='belum terkonfirmasi'):
        client.logout_employee(directory, Unavailable())
    assert saved.exists()


def test_windows_partial_install_does_not_remove_unowned_service(tmp_path, monkeypatch):
    from vanguard import windows
    backend = WindowsTunnel()
    monkeypatch.setattr(windows.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(windows, 'run', lambda *args: pytest.fail('must not uninstall unknown owner'))
    with pytest.raises(Rejected, match='ownership'):
        backend.down(tmp_path / 'vanguard-client.conf')
