import json

import pytest
from conftest import register

from deploy.firewall import rules
from vanguard.client import admit, initialize, login_employee
from vanguard.common import Rejected


def test_two_clients_have_independent_admission_and_revocation(lab, tmp_path):
    register(lab)
    first = admit(lab['directory'], lab['remote'])
    assert first['tunnel_ip'] == '10.8.0.2'
    existing = dict(lab['wg'].active)
    windows = tmp_path / 'windows-client'
    initialize(windows, 'vm-client-windows', '10.8.0.4')
    request = json.loads((windows / 'request.json').read_text())
    issued = lab['ca'].issue('vm-client-windows', request['csr'])
    (windows / 'device.crt').write_text(issued['certificate'])
    lab['admission'].employees.create('windows-test-account', 'windows-test-password')
    lab['management'].call('POST', '/api/devices', {
        'device_id': 'vm-client-windows', 'certificate': issued['certificate'],
        'wg_public_key': request['wg_public_key'], 'tunnel_ip': '10.8.0.4',
    })
    # Registration must not add a live peer, even alongside an admitted Linux client.
    assert lab['wg'].active == existing
    lab['management'].call('POST', '/api/devices/vm-client-windows/employee',
                           {'username': 'windows-test-account'})
    login_employee(windows, lab['remote'], 'windows-test-account', 'windows-test-password')
    assert admit(windows, lab['remote'])['tunnel_ip'] == '10.8.0.4'
    assert len(lab['wg'].active) == 2
    lab['ca'].revoke(issued['serial'])
    with pytest.raises(Rejected):
        admit(windows, lab['remote'])
    lab['admission'].reconcile()
    assert lab['wg'].active == existing


def test_windows_firewall_extension_keeps_lan_bypass_blocked():
    legacy = rules('server', '192.168.100.1')
    extended = rules('server', '192.168.100.1', windows_client=True)
    assert '192.168.100.60' not in legacy and '10.8.0.4' not in legacy
    assert '192.168.100.60' in extended
    assert 'iifname "wg0" ip saddr { 10.8.0.2, 10.8.0.4 } ip daddr 10.8.0.1' in extended
    assert extended.index('ip daddr 10.8.0.0/24 iifname != "wg0" counter drop') < extended.index('ct state established')
    assert 'type filter hook forward priority -10; policy drop' in extended
    for role in ('ca', 'admin', 'client', 'attacker'):
        assert rules(role, '192.168.100.1', windows_client=True) == rules(role, '192.168.100.1')
