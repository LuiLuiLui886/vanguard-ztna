import json
import time

import pytest
from conftest import proof, register

from vanguard.client import admit, login_employee
from vanguard.common import Rejected, database


def test_s01_valid_employee_password_without_device_proof_is_rejected(lab):
    register(lab)
    login = lab['remote'].call('POST', '/api/employee/login', {
        'username': 'employee-test', 'password': 'employee-test-password',
    })
    assert login['session_token'] and lab['wg'].additions == []
    response = lab['app'].test_client().post('/api/challenge', json={
        'employee_session': login['session_token'], 'wg_public_key': lab['request']['wg_public_key'],
    })
    assert response.status_code == 400
    # Even a copied certificate and a fresh, valid employee session are insufficient.
    lab['employee_session'] = login['session_token']
    body = proof(lab)
    body['signature'] = 'aW52YWxpZA=='
    with pytest.raises(Rejected):
        lab['admission'].verify(body)
    assert lab['wg'].additions == []


def test_employee_session_is_required_and_bound_to_device(lab):
    register(lab)
    for token in [None, 'x' * 43]:
        with pytest.raises(Rejected):
            lab['admission'].challenge({'certificate': lab['issued']['certificate'],
                                       'wg_public_key': lab['request']['wg_public_key'],
                                       'employee_session': token})
    lab['admission'].employees.create('other-user', 'other-user-password')
    other = lab['admission'].employees.login('other-user', 'other-user-password', 'other')
    lab['employee_session'] = other['session_token']
    with pytest.raises(Rejected):
        proof(lab)
    assert lab['wg'].additions == []


def test_employee_challenge_cannot_switch_session(lab):
    register(lab)
    body = proof(lab)
    token = lab['admission'].employees.login(
        'employee-test', 'employee-test-password', 'another-source')['session_token']
    with pytest.raises(Rejected, match='does not match challenge'):
        lab['admission'].verify({**body, 'employee_session': token})
    with pytest.raises(Rejected, match='consumed'):
        lab['admission'].verify(body)
    assert lab['wg'].additions == []


def test_employee_disable_blocks_pending_proof_and_removes_live_peer(lab):
    register(lab)
    admit(lab['directory'], lab['remote'])
    pending = proof(lab)
    assert lab['wg'].active
    lab['management'].call('POST', '/api/employees/employee-test/disable', {})
    assert not lab['wg'].active
    with pytest.raises(Rejected):
        lab['admission'].verify(pending)
    with pytest.raises(Rejected):
        lab['remote'].call('POST', '/api/employee/login', {
            'username': 'employee-test', 'password': 'employee-test-password',
        })


def test_employee_expiry_bounds_lease_and_daemon_removes_peer(lab):
    register(lab)
    until = time.time() + 30
    with database(lab['admission'].db) as db:
        db.execute('UPDATE employee_sessions SET expires=?', (until,))
    admitted = admit(lab['directory'], lab['remote'])
    assert admitted['lease_until'] <= until
    with database(lab['admission'].db) as db:
        db.execute('UPDATE employee_sessions SET expires=0')
    lab['admission'].reconcile()
    assert not lab['wg'].active
    with database(lab['admission'].db) as db:
        row = db.execute("SELECT detail FROM audit WHERE event='peer_removed'").fetchone()
    assert json.loads(row[0])['reason'] == 'employee_session_invalid'


def test_employee_credentials_and_session_are_not_exposed(lab):
    register(lab)
    login_employee(lab['directory'], lab['remote'], 'employee-test', 'employee-test-password')
    session_file = lab['directory'] / 'employee-session.json'
    assert session_file.stat().st_mode & 0o777 == 0o600
    assert 'employee-test-password' not in session_file.read_text()
    token = json.loads(session_file.read_text())['session_token']
    assert token.encode() not in lab['admission'].db.read_bytes()
    admit(lab['directory'], lab['remote'])
    listing = lab['management'].call('GET', '/api/employees')
    assert listing == {'employees': [{'username': 'employee-test', 'enabled': 1}]}
    audit = json.dumps(lab['management'].call('GET', '/api/audit'))
    assert token not in audit and 'employee-test-password' not in audit


def test_employee_lockout_and_binding_are_persistent(lab):
    register(lab)
    employees = lab['admission'].employees
    for _ in range(5):
        with pytest.raises(Rejected) as failure:
            employees.login('employee-test', 'wrong', 'bad-source')
        assert failure.value.status == 401
    with pytest.raises(Rejected) as failure:
        employees.login('employee-test', 'employee-test-password', 'fresh-source')
    assert failure.value.status == 429
    employees.create('another-user', 'another-user-password')
    with pytest.raises(Rejected, match='immutable'):
        lab['admission'].bind_employee('vm-client', 'another-user')


@pytest.mark.parametrize('method,path,body', [
    ('GET', '/api/employees', None),
    ('POST', '/api/employees', {'username': 'x', 'password': 'test-password-long'}),
    ('POST', '/api/employees/employee-test/disable', {}),
    ('POST', '/api/devices/vm-client/employee', {'username': 'employee-test'}),
])
def test_employee_sessions_cannot_manage_accounts(lab, method, path, body):
    response = lab['app'].test_client().open(method=method, path=path, json=body,
        headers={'Authorization': 'Bearer ' + lab['employee_session']})
    assert response.status_code == 401


def test_legacy_identity_without_employee_binding_fails_closed(lab):
    lab['admission'].register({
        'device_id': 'vm-client', 'certificate': lab['issued']['certificate'],
        'wg_public_key': lab['request']['wg_public_key'], 'tunnel_ip': '10.8.0.2',
    })
    with pytest.raises(Rejected, match='Employee session or device binding rejected'):
        proof(lab)
    assert not lab['wg'].active
    lab['admission'].bind_employee('vm-client', 'employee-test')
    assert admit(lab['directory'], lab['remote'])['decision'] == 'ACCEPT'


def test_session_expiring_during_crl_fetch_cannot_add_peer(lab):
    register(lab)
    body = proof(lab)
    crl = lab['ca'].crl()

    def expire_session():
        with database(lab['admission'].db) as db:
            db.execute('UPDATE employee_sessions SET expires=0')
        return crl

    lab['admission'].fetch_crl = expire_session
    with pytest.raises(Rejected, match='Employee session or device binding rejected'):
        lab['admission'].verify(body)
    assert lab['wg'].additions == []
