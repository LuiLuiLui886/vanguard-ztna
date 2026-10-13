import base64
import json
import os
import time

import pytest

from vanguard import client
from vanguard.common import Rejected
from vanguard.windows import WindowsTunnel

SERVER_KEY = base64.b64encode(b's' * 32).decode()


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
    assert len(list(directory.iterdir())) == 1


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
