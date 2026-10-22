import base64
import json
import zipfile
from types import SimpleNamespace

import pytest
from conftest import LocalRemote

from vanguard import client
from vanguard.admin import Dashboard
from vanguard.ca import create_app as ca_app
from vanguard.common import Rejected
from vanguard.onboarding import import_bundle
from vanguard.pki import fingerprint, load_cert
from vanguard.profile import load_profile, validate_profile


def profile(root='a' * 64):
    return {'schema': 1, 'api_url': 'https://vpn.example.test:8443',
            'wireguard_host': 'vpn.example.test', 'wireguard_port': 51821,
            'server_public_key': base64.b64encode(b's' * 32).decode(), 'root_sha256': root,
            'backend_network': '192.168.100.0/24', 'tunnel_network': '10.8.0.0/24',
            'allowed_ips': ['10.8.0.1/32'],
            'resources': [{'name': 'internal-demo', 'address': '10.8.0.1',
                           'protocol': 'tcp', 'port': 8082}]}


@pytest.mark.parametrize('field,value', [
    ('schema', True), ('api_url', 'http://example.test'),
    ('api_url', 'https://user:secret@example.test'), ('api_url', 'https://example.test:0'),
    ('api_url', 'https://example.test/path'), ('api_url', 'https://example.test/#x'),
    ('wireguard_host', 'host\nPostUp = malicious'), ('wireguard_host', '999.1.2.3'),
    ('wireguard_port', True), ('wireguard_port', 65536), ('root_sha256', 'unset'),
    ('server_public_key', 'unset'), ('allowed_ips', ['0.0.0.0/0']),
    ('allowed_ips', ['192.168.50.0/24']), ('backend_network', '10.8.0.0/24'),
    ('tunnel_network', '10.9.0.0/24'), ('resources', [{'name': 'wrong'}]),
])
def test_profile_rejects_unsafe_or_incompatible_input(field, value):
    data = profile()
    data[field] = value
    with pytest.raises(Rejected):
        validate_profile(data)


def test_custom_profile_controls_both_transports_before_admission(lab, monkeypatch):
    data = profile()
    seen = []
    class Tunnel:
        name = 'custom'
        def preflight(self):
            seen.append('preflight')
        def up(self, path):
            seen.append(path.read_text())
            raise KeyboardInterrupt()
        def down(self, path):
            seen.append('down')
    def admit(*args):
        seen.append('admit')
        return {'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999}
    monkeypatch.setattr(client, 'admit', admit)
    with pytest.raises(KeyboardInterrupt):
        client.connect(lab['directory'], SimpleNamespace(url=data['api_url']),
                       data['server_public_key'], Tunnel(), profile=data)
    assert seen[0:2] == ['preflight', 'admit']
    assert 'Endpoint = vpn.example.test:51821' in seen[2]
    assert 'AllowedIPs = 10.8.0.1/32' in seen[2]
    assert '192.168.100.20' not in seen[2]
    assert seen[-1] == 'down'
    assert not (lab['directory'] / 'custom.conf').exists()


def test_profile_mismatch_never_calls_admission(lab, monkeypatch):
    monkeypatch.setattr(client, 'admit', lambda *args: pytest.fail('admission called'))
    with pytest.raises(Rejected, match='differs'):
        client.connect(lab['directory'], SimpleNamespace(url='https://other.test'),
                       profile()['server_public_key'], SimpleNamespace(name='custom'), profile=profile())


def public_bundle(lab, tmp_path):
    root = lab['ca'].path / 'root.crt'
    data = profile(fingerprint(load_cert(root.read_bytes())))
    dash = Dashboard(tmp_path / 'dashboard', LocalRemote(ca_app(
        {'CA_DIR': lab['ca'].path, 'TOKEN': 'c' * 32}), 'c' * 32),
        lab['management'], client_profile=data)
    request = dict(lab['request'], display_name='Endpoint', department='Test',
                   owner='Tester', platform='Windows')
    dash.register(request)
    bundle = tmp_path / 'public.zip'
    bundle.write_bytes(dash.bundle('vm-client'))
    return bundle, root, data


def test_profiled_bundle_import_is_idempotent_offline_and_keeps_keys(lab, tmp_path):
    bundle, root, data = public_bundle(lab, tmp_path)
    directory = lab['directory']
    before = {name: (directory / name).read_bytes() for name in
              ('identity.key', 'wg.key', 'request.json', 'employee-session.json')}
    (directory / 'device.crt').unlink()
    result = import_bundle(directory, bundle, root, data)
    assert result == {'imported': True, 'unchanged': False, 'admission_required': True}
    assert import_bundle(directory, bundle, root, data)['unchanged']
    assert all((directory / name).read_bytes() == value for name, value in before.items())
    assert lab['wg'].active == {}
    assert not (directory / 'root.crt').exists()


@pytest.mark.parametrize('tamper', ['binding', 'profile', 'path', 'certificate', 'key'])
def test_tampered_import_never_overwrites_identity_or_certificate(lab, tmp_path, tamper):
    bundle, root, data = public_bundle(lab, tmp_path)
    with zipfile.ZipFile(bundle) as z:
        files = {name: z.read(name) for name in z.namelist()}
    manifest = json.loads(files['manifest.json'])
    if tamper == 'binding':
        manifest['device_id'] = 'another-device'
    elif tamper == 'profile':
        manifest['profile']['wireguard_host'] = 'other.test'
    elif tamper == 'path':
        files['../identity.key'] = b'bad'
    elif tamper == 'certificate':
        files['device.crt'] = root.read_bytes()
    else:
        (lab['directory'] / 'wg.key').write_text(base64.b64encode(b'z' * 32).decode())
    files['manifest.json'] = json.dumps(manifest).encode()
    with zipfile.ZipFile(bundle, 'w') as z:
        for name, value in files.items():
            z.writestr(name, value)
    before = {p.name: p.read_bytes() for p in lab['directory'].iterdir() if p.is_file()}
    with pytest.raises(Rejected):
        import_bundle(lab['directory'], bundle, root, data)
    assert all((lab['directory'] / name).read_bytes() == value for name, value in before.items())
    assert not lab['wg'].active


def test_profile_root_pin_is_independent_of_bundle(lab, tmp_path):
    p = tmp_path / 'profile.json'
    p.write_text(json.dumps(profile()))
    with pytest.raises(Rejected, match='root'):
        load_profile(p, lab['ca'].path / 'root.crt')


def test_disconnect_request_is_scoped_to_connect_owner(lab, monkeypatch):
    directory = lab['directory']
    seen = []
    class Tunnel:
        name = 'owned'
        def preflight(self):
            pass
        def up(self, path):
            seen.append('up')
        def down(self, path):
            seen.append('down')
    monkeypatch.setattr(client, 'admit', lambda *args: {
        'decision': 'ACCEPT', 'tunnel_ip': '10.8.0.2', 'lease_until': 9999999999})
    def stop(_):
        owner = json.loads((directory / '.connection.json').read_text())['owner']
        (directory / '.disconnect.json').write_text(json.dumps({'owner': owner}))
    monkeypatch.setattr(client.time, 'sleep', stop)
    client.connect(directory, None, profile()['server_public_key'], Tunnel())
    assert seen == ['up', 'down']
    assert not (directory / '.connection.json').exists()
    assert not (directory / 'owned.conf').exists()
    assert (directory / 'employee-session.json').exists()


def test_custom_tls_requires_allowlist_and_hostname_verification(lab, tmp_path):
    import subprocess

    ca = lab['ca']
    csr = tmp_path / 'server.csr'
    csr.write_text(lab['request']['csr'])
    certificate = tmp_path / 'server.crt'
    before = (ca.path / 'serial').read_bytes()
    with pytest.raises(Rejected, match='allowlist'):
        ca.sign_tls(csr, 'vpn.example.test', certificate)
    assert (ca.path / 'serial').read_bytes() == before
    ca.sign_tls(csr, 'vpn.example.test', certificate, approved_hosts=['vpn.example.test'])
    command = ['openssl', 'verify', '-CAfile', str(ca.path / 'root.crt'), '-verify_hostname']
    assert subprocess.run([*command, 'vpn.example.test', str(certificate)], capture_output=True).returncode == 0
    assert subprocess.run([*command, 'wrong.example.test', str(certificate)], capture_output=True).returncode != 0
    with pytest.raises(Rejected):
        ca.sign_tls(csr, 'vpn.example.test\nkeyUsage=invalid', tmp_path / 'bad.crt',
                    approved_hosts=['vpn.example.test\nkeyUsage=invalid'])


def test_pilot_generator_preserves_network_and_produces_matching_profile(lab, tmp_path):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path('scripts').resolve()))
    from prepare_endpoint_pilot import prepare
    output = tmp_path / 'pilot'
    data = prepare(lab['ca'].path / 'root.crt', profile()['server_public_key'], output)
    assert load_profile(output / 'profile.json', output / 'root.crt') == data
    plan = json.loads((output / 'network-plan.json').read_text())
    assert plan['allocation_confirmed'] is False
    assert plan['endpoint_route']['destination'] == '192.168.100.20/32'
    assert plan['reserved_tunnel_ips'] == ['10.8.0.2', '10.8.0.3', '10.8.0.4']
    with pytest.raises(ValueError):
        prepare(lab['ca'].path / 'root.crt', profile()['server_public_key'], output)


def test_pilot_firewall_only_opens_approved_sources_and_preserves_gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location('endpoint_firewall', 'deploy/firewall.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module.rules('server', '192.168.100.1', True, True)
    candidate = module.rules('server', '192.168.100.1', True, True, ['192.168.50.20','192.168.50.30'])
    assert candidate.count('192.168.50.20') == 2
    assert candidate.replace(', 192.168.50.20, 192.168.50.30', '') == original
    assert 'tcp dport 8082 jump application_gate' in candidate
    with pytest.raises(ValueError):
        module.rules('server', '192.168.100.1', physical_clients=['0.0.0.0'])
    with pytest.raises(ValueError):
        module.rules('ca', '192.168.100.1', physical_clients=['192.168.50.20'])


@pytest.mark.parametrize('addresses,routes', [
    (['192.168.100.5/24'], ['0.0.0.0/0']),
    (['10.8.0.99/24'], ['0.0.0.0/0']),
    (['192.168.50.20/24'], ['10.0.0.0/8']),
    (['192.168.50.20/24'], ['10.8.0.1/32']),
    (['invalid'], ['0.0.0.0/0']),
])
def test_network_preflight_rejects_conflicts(addresses, routes):
    from vanguard.profile import check_network_conflicts
    with pytest.raises(Rejected):
        check_network_conflicts(profile(), addresses, routes)


def test_network_preflight_allows_specific_backend_route_without_mutation():
    from vanguard.profile import check_network_conflicts
    addresses = ['192.168.50.20/24', '127.0.0.1/8']
    routes = ['0.0.0.0/0', '192.168.50.0/24', '192.168.100.20/32']
    assert check_network_conflicts(profile(), addresses, routes) is None
    assert len(addresses) == 2 and len(routes) == 3


def test_profile_init_requires_allocation_before_key_creation(tmp_path, monkeypatch):
    import sys
    data = profile()
    monkeypatch.setattr('vanguard.profile.load_profile', lambda *args: data)
    target = tmp_path / 'identity'
    monkeypatch.setattr(sys, 'argv', ['vanguard-client', '--profile', 'test.json',
                                     '--directory', str(target), 'init'])
    with pytest.raises(SystemExit) as exc:
        client.main()
    assert exc.value.code == 1
    assert not target.exists()
