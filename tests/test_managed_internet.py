import json
from types import SimpleNamespace

import pytest
from conftest import register
from test_endpoint_profile import profile

from deploy.firewall import rules
from vanguard import client, internet
from vanguard.common import Rejected, database
from vanguard.internet import NftInternet
from vanguard.profile import validate_profile


def managed():
    return dict(profile(), schema=2, api_url='https://192.168.100.20:8081',
                wireguard_host='192.168.100.20', allowed_ips=['0.0.0.0/1', '128.0.0.0/1'],
                internet={'mode': 'managed-ipv4', 'dns': ['1.1.1.1']})


def test_managed_profile_is_opt_in_and_ipv4_only():
    assert validate_profile(managed())['schema'] == 2
    assert validate_profile(profile())['schema'] == 1
    for update in ({'schema': 1}, {'allowed_ips': ['0.0.0.0/0']},
                   {'api_url': 'https://dynamic.example.test'},
                   {'wireguard_host': '10.8.0.1'},
                   {'internet': {'mode': 'managed-ipv4', 'dns': ['192.168.1.1']}}):
        with pytest.raises(Rejected):
            validate_profile(dict(managed(), **update))


def test_missing_lockdown_rejected_before_admission(lab, monkeypatch):
    monkeypatch.setattr(client, 'admit', lambda *a: pytest.fail('admission called'))
    p = managed()
    with pytest.raises(Rejected, match='lockdown'):
        client.connect(lab['directory'], SimpleNamespace(url=p['api_url']), p['server_public_key'],
                       SimpleNamespace(name='test'), profile=p)


def test_managed_connect_guards_before_admission_and_sets_dns(lab, monkeypatch):
    events = []
    class Backend:
        name = 'test'
        def require_internet(self, p):
            events.append('guard')
        def preflight(self):
            events.append('preflight')
        def up(self, path):
            events.append(path.read_text())
            raise KeyboardInterrupt()
        def down(self, path):
            events.append('down')
    def admit(*args):
        events.append('admit')
        return {'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999}
    monkeypatch.setattr(client, 'admit', admit)
    p = managed()
    with pytest.raises(KeyboardInterrupt):
        client.connect(lab['directory'], SimpleNamespace(url=p['api_url']), p['server_public_key'],
                       Backend(), profile=p)
    assert events[:3] == ['guard', 'preflight', 'admit']
    assert 'DNS = 1.1.1.1' in events[3]
    assert 'AllowedIPs = 0.0.0.0/1, 128.0.0.0/1' in events[3]
    assert events[-1] == 'down'


@pytest.mark.parametrize('reason', ['logout', 'revoke', 'disabled', 'account_disabled', 'expired', 'session_expired', 'ca_down'])
def test_internet_grant_tracks_real_admission_lifecycle(lab, tmp_path, monkeypatch, reason):
    path = tmp_path / 'internet.json'
    path.write_text(json.dumps({'grants': [{'device_id': 'vm-client', 'username': 'employee-test',
                                          'resource': 'internet-ipv4'}]}))
    commands = []
    monkeypatch.setattr(internet, 'run', lambda args, **kw: commands.append(kw['input'].decode()))
    lab['admission'].resources = NftInternet(path)
    register(lab)
    assert commands == [] and not lab['wg'].active
    client.admit(lab['directory'], lab['remote'])
    assert '10.8.0.2 timeout' in commands[-1]
    if reason == 'logout':
        lab['admission'].logout_employee(lab['employee_session'])
    elif reason == 'account_disabled':
        lab['admission'].disable_employee('employee-test')
    elif reason == 'disabled':
        lab['admission'].disable('vm-client')
    else:
        if reason == 'revoke':
            lab['ca'].revoke(lab['issued']['serial'])
        elif reason == 'expired':
            with database(lab['admission'].db) as db:
                db.execute('UPDATE devices SET lease_until=0')
        elif reason == 'session_expired':
            with database(lab['admission'].db) as db:
                db.execute('UPDATE employee_sessions SET expires=0')
        else:
            def unavailable():
                raise Rejected('Unavailable', 503)
            lab['admission'].fetch_crl = unavailable
        lab['admission'].reconcile()
    assert commands[-1] == 'flush set inet vanguard internet_access\n'
    assert not lab['wg'].active


def test_empty_or_invalid_grant_never_authorizes_internet(lab, tmp_path, monkeypatch):
    path = tmp_path / 'internet.json'
    path.write_text('{"grants": []}')
    commands = []
    monkeypatch.setattr(internet, 'run', lambda args, **kw: commands.append(kw['input'].decode()))
    lab['admission'].resources = NftInternet(path)
    register(lab)
    client.admit(lab['directory'], lab['remote'])
    assert commands[-1] == 'flush set inet vanguard internet_access\n'
    path.write_text('{"grants": [{"device_id": "*"}]}')
    with pytest.raises(Rejected):
        client.admit(lab['directory'], lab['remote'])
    assert not lab['wg'].active
    assert commands[-1] == 'flush set inet vanguard internet_access\n'


def test_gateway_has_no_unconditional_established_bypass():
    content = rules('server', '192.168.100.1', True, True, internet_uplink='eth0')
    forward = content.split('chain forward {')[1]
    assert 'ip daddr @internet_access ct state established,related counter accept' in forward
    assert 'ip saddr @internet_access' in forward
    assert 'meta nfproto ipv6 counter drop' in forward
    assert 'iifname "wg0" ip daddr @non_internet counter drop' in forward
    assert 'flow add' not in content and 'flags timeout' in content
    for uplink in ('wg0', 'lo', 'eth0"; accept'):
        with pytest.raises(ValueError):
            rules('server', '192.168.100.1', True, True, internet_uplink=uplink)


def test_admin_internet_grant_does_not_install_peer(lab, tmp_path, monkeypatch):
    path = tmp_path / 'internet.json'
    path.write_text('{"grants": []}')
    commands = []
    monkeypatch.setattr(internet, 'run', lambda args, **kw: commands.append(kw['input'].decode()))
    lab['admission'].resources = NftInternet(path)
    register(lab)
    result = lab['management'].call('POST', '/api/devices/vm-client/internet', {'enabled': True})
    assert result['admission_required'] and not lab['wg'].active
    assert commands[-1] == 'flush set inet vanguard internet_access\n'
    client.admit(lab['directory'], lab['remote'])
    assert '10.8.0.2 timeout' in commands[-1]
    lab['management'].call('POST', '/api/devices/vm-client/internet', {'enabled': False})
    assert commands[-1] == 'flush set inet vanguard internet_access\n'
    assert lab['wg'].active  # Internet-only removal does not revoke internal VPN identity.
    for bad in ('true', 1, None):
        with pytest.raises(Rejected):
            lab['management'].call('POST', '/api/devices/vm-client/internet', {'enabled': bad})
    with pytest.raises(Rejected):
        lab['remote'].call('POST', '/api/devices/vm-client/internet', {'enabled': True})


def test_attach_failure_keeps_cleanup_owned(lab, monkeypatch):
    """Real Windows backend ordering with command boundary faults, not native evidence."""
    from vanguard import windows
    monkeypatch.setenv('ProgramData', str(lab['directory'] / 'program-data'))
    events = []
    backend = windows.WindowsTunnel()
    backend.internet_required = True
    monkeypatch.setattr(backend, 'require_internet', lambda p: None)
    monkeypatch.setattr(backend, 'preflight', lambda: None)
    monkeypatch.setattr(client, 'admit', lambda *args: {
        'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999})
    def command(args, **kwargs):
        events.append(args)
        if args[-1] == 'attach':
            raise Rejected('Adapter not ready')
    monkeypatch.setattr(windows, 'run', command)
    monkeypatch.setattr(windows.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1060))
    p = managed()
    with pytest.raises(Rejected, match='Adapter not ready'):
        client.connect(lab['directory'], SimpleNamespace(url=p['api_url']), p['server_public_key'],
                       backend, profile=p)
    assert events[0][1] == '/installtunnelservice'
    assert events[2][-1] == 'attach'
    assert events[3][-1] == 'detach'
    assert events[4][1] == '/uninstalltunnelservice'
    assert not (lab['directory'] / 'vanguard-client.conf').exists()


def test_internet_policy_failure_drops_all_grant_classes(lab, tmp_path, monkeypatch):
    from vanguard.internet import AccessPolicies
    path = tmp_path / 'invalid.json'
    path.write_text('{}')
    commands = []
    monkeypatch.setattr(internet, 'run', lambda args, **kw: commands.append(kw['input'].decode()))
    class Application:
        def sync(self, db, peers):
            commands.append('application-added')
        def clear(self):
            commands.append('application-cleared')
    with pytest.raises(Rejected):
        AccessPolicies([Application(), NftInternet(path)]).sync(lab['admission'].db, set())
    assert commands[0] == 'application-added'
    assert 'application-cleared' in commands
    assert commands[-1] == 'flush set inet vanguard internet_access\n'


def test_grant_status_uses_employee_binding_and_unknown_on_bad_policy(lab, tmp_path):
    path = tmp_path / 'policy.json'
    lab['admission'].resources = NftInternet(path)
    register(lab)
    path.write_text(json.dumps({'grants': [{'device_id': 'vm-client', 'username': 'another-user',
                                          'resource': 'internet-ipv4'}]}))
    assert lab['admission'].listing()[0]['internet_granted'] is False
    path.write_text(json.dumps({'grants': [{'device_id': '*', 'username': 'employee-test',
                                          'resource': 'internet-ipv4'}]}))
    assert lab['admission'].listing()[0]['internet_granted'] is None


def test_removing_one_internet_grant_preserves_other_device(lab, tmp_path, monkeypatch):
    path = tmp_path / 'policy.json'
    path.write_text('{"grants": []}')
    commands = []
    monkeypatch.setattr(internet, 'run', lambda args, **kw: commands.append(kw['input'].decode()))
    lab['admission'].resources = NftInternet(path)
    register(lab)
    other = tmp_path / 'other-client'
    client.initialize(other, 'another-device', '10.8.0.4')
    request = json.loads((other / 'request.json').read_text())
    issued = lab['ca'].issue('another-device', request['csr'])
    (other / 'device.crt').write_text(issued['certificate'])
    lab['admission'].register(dict(request, certificate=issued['certificate']))
    lab['admission'].employees.create('another-user', 'another-long-test-password')
    lab['admission'].bind_employee('another-device', 'another-user')
    client.login_employee(other, lab['remote'], 'another-user', 'another-long-test-password')
    for name, directory in [('vm-client', lab['directory']), ('another-device', other)]:
        lab['admission'].set_internet(name, True)
        client.admit(directory, lab['remote'])
    assert '10.8.0.2 timeout' in commands[-1] and '10.8.0.4 timeout' in commands[-1]
    lab['admission'].set_internet('vm-client', False)
    assert '10.8.0.2 timeout' not in commands[-1] and '10.8.0.4 timeout' in commands[-1]
    assert len(lab['wg'].active) == 2


def test_detach_failure_stops_owned_tunnel_but_preserves_config(lab, monkeypatch):
    from vanguard import windows
    monkeypatch.setenv('ProgramData', str(lab['directory'] / 'program-data'))
    events = []
    backend = windows.WindowsTunnel()
    backend.internet_required = True
    monkeypatch.setattr(backend, 'require_internet', lambda p: None)
    monkeypatch.setattr(backend, 'preflight', lambda: None)
    monkeypatch.setattr(client, 'admit', lambda *args: {
        'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999})
    def command(args, **kwargs):
        events.append(args)
        if args[-1] == 'attach':
            raise KeyboardInterrupt()
        if args[-1] == 'detach':
            raise Rejected('Policy service unavailable')
    monkeypatch.setattr(windows, 'run', command)
    monkeypatch.setattr(windows.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1060))
    p = managed()
    with pytest.raises(Rejected, match='policy cleanup unconfirmed'):
        client.connect(lab['directory'], SimpleNamespace(url=p['api_url']), p['server_public_key'],
                       backend, profile=p)
    assert events[-1][1] == '/uninstalltunnelservice'
    assert (lab['directory'] / 'vanguard-client.conf').exists()
    assert (lab['directory'] / '.connection.json').exists()


@pytest.mark.parametrize('field,value', [
    ('dns', [16843009]),  # ipaddress accepts this integer as 1.1.1.1.
    ('dns', ['1.1.1.1', 134744072]),
    ('allowed_ips', [168296449]),  # Integer representation of 10.8.0.1/32.
    ('backend_network', 3232235520),
    ('backend_network', True),
    ('tunnel_network', ['10.8.0.0', 24]),
])
def test_profile_rejects_non_text_network_values(field, value):
    p = profile() if field == 'allowed_ips' else managed()
    if field == 'dns':
        p['internet']['dns'] = value
    else:
        p[field] = value
    with pytest.raises(Rejected, match='Invalid endpoint profile'):
        validate_profile(p)


@pytest.mark.parametrize('failed_check', [2, 4])
def test_failed_lockdown_recheck_never_requests_new_lease(lab, monkeypatch, failed_check):
    events = []
    class Backend:
        name = 'test-renewal'
        def require_internet(self, p):
            events.append('guard')
            if events.count('guard') == failed_check:
                raise Rejected('Managed firewall inspection failed')
        def preflight(self):
            pass
        def up(self, config):
            events.append('up')
        def down(self, config):
            events.append('down')
    def admit(*args):
        events.append('admit')
        return {'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999}
    monkeypatch.setattr(client, 'admit', admit)
    monkeypatch.setattr(client.time, 'sleep', lambda seconds: None)
    p = managed()
    with pytest.raises(Rejected, match='firewall inspection failed'):
        client.connect(lab['directory'], SimpleNamespace(url=p['api_url']),
                       p['server_public_key'], Backend(), p)
    assert events.count('admit') == failed_check - 1, 'Failed policy check must not request a new lease'
    assert events[:3] == ['guard', 'admit', 'up']
    assert events[3:-2] == ['guard', 'admit'] * (failed_check - 2)
    assert events[-2] == 'guard'
    assert events[-1] == 'down'
    assert not (lab['directory'] / 'test-renewal.conf').exists()
