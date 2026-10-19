import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import proof, register

from vanguard.client import admit, logout_employee
from vanguard.common import Rejected, database


def test_logout_revokes_pending_proof_access_and_is_idempotent(lab):
    register(lab)
    admit(lab['directory'], lab['remote'])
    pending = proof(lab)
    body = {'employee_session': lab['employee_session']}
    for _ in range(2):
        result = lab['remote'].call('POST', '/api/employee/logout', body)
        assert result == {'revoked': True, 'peer_removal_confirmed': True}
    assert not lab['wg'].active
    with pytest.raises(Rejected):
        lab['admission'].verify(pending)
    with database(lab['admission'].db) as db:
        assert not db.execute('SELECT * FROM employee_challenges').fetchall()
        assert not db.execute('SELECT * FROM employee_sessions').fetchall()
    assert logout_employee(lab['directory'], lab['remote'])['revoked']
    assert not (lab['directory'] / 'employee-session.json').exists()


def test_old_session_logout_preserves_new_session_lease(lab):
    register(lab)
    old = lab['employee_session']
    newer = lab['admission'].employees.login('employee-test', 'employee-test-password', 'test')
    lab['employee_session'] = newer['session_token']
    lab['admission'].verify(proof(lab))
    lab['admission'].logout_employee(old)
    assert lab['wg'].active
    lab['admission'].employees.require(newer['session_token'], 'vm-client')


def test_logout_kernel_failure_retry_and_other_session_takeover(lab, monkeypatch):
    register(lab)
    admit(lab['directory'], lab['remote'])
    remove = lab['wg'].remove
    monkeypatch.setattr(lab['wg'], 'remove', lambda _: (_ for _ in ()).throw(Rejected('wg failed')))
    with pytest.raises(Rejected, match='unconfirmed'):
        lab['admission'].logout_employee(lab['employee_session'])
    with pytest.raises(Rejected):
        proof(lab)
    monkeypatch.setattr(lab['wg'], 'remove', remove)
    assert lab['admission'].logout_employee(lab['employee_session'])['revoked']
    assert not lab['wg'].active


def test_concurrent_logout_waits_for_renewal_then_removes_access(lab):
    register(lab)
    pending = proof(lab)
    inside, release = threading.Event(), threading.Event()
    crl = lab['ca'].crl()
    def blocked_fetch():
        inside.set()
        assert release.wait(5)
        return crl
    lab['admission'].fetch_crl = blocked_fetch
    with ThreadPoolExecutor(max_workers=2) as pool:
        verifying = pool.submit(lab['admission'].verify, pending)
        assert inside.wait(5)
        logging_out = pool.submit(lab['admission'].logout_employee, lab['employee_session'])
        release.set()
        assert verifying.result()['decision'] == 'ACCEPT'
        assert logging_out.result()['revoked']
    assert not lab['wg'].active


def test_unknown_logout_token_is_rejected_without_affecting_access(lab):
    register(lab)
    admit(lab['directory'], lab['remote'])
    with pytest.raises(Rejected):
        lab['admission'].logout_employee('unknown-session-token-' * 2)
    assert lab['wg'].active
