import json
import re
from concurrent.futures import ThreadPoolExecutor

from conftest import proof, register

from vanguard.common import database


def timings(lab):
    with database(lab['admission'].db) as db:
        return [json.loads(r[0]) for r in db.execute(
            "SELECT detail FROM audit WHERE event='admission_timing' ORDER BY id")]


def test_denial_timing_correlates_without_credential_leak(lab):
    register(lab)
    body = proof(lab)
    body['signature'] = 'aW52YWxpZA=='
    response = lab['app'].test_client().post('/api/verify', json=body,
                                           headers={'X-VanGuard-Request-ID': 'caller-secret'})
    assert response.status_code == 403 and not lab['wg'].active
    request_id = response.headers['X-VanGuard-Request-ID']
    assert re.fullmatch('[a-f0-9]{32}', request_id)
    row, = timings(lab)
    assert row['request_id'] == request_id and row['endpoint'] == 'verify'
    assert row['reason'] == 'proof_invalid'
    assert row['detect_ns'] >= 0 and row['respond_ns'] >= 0
    assert row['total_ns'] == row['detect_ns'] + row['respond_ns']
    recorded = json.dumps(row)
    for secret in (lab['employee_session'], body['certificate'], body['challenge_id'],
                   body['signature'], 'caller-secret', 'employee-test-password'):
        assert secret not in recorded


def test_success_and_management_endpoints_not_counted_as_incidents(lab):
    register(lab)
    response = lab['app'].test_client().post('/api/verify', json=proof(lab))
    assert response.status_code == 200 and lab['wg'].active
    assert timings(lab) == []
    response = lab['app'].test_client().get('/api/devices')
    assert response.status_code == 401 and 'X-VanGuard-Request-ID' not in response.headers
    assert timings(lab) == []


def test_concurrent_denials_have_independent_request_ids(lab, monkeypatch):
    def deny(_):
        with lab['app'].test_client() as client:
            response = client.post('/api/challenge', json={})
            assert response.status_code == 400
            return response.headers['X-VanGuard-Request-ID']
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(deny, range(8)))
    assert len(set(ids)) == 8
    rows = timings(lab)
    assert {r['request_id'] for r in rows} == set(ids)
    assert all(r['total_ns'] == r['detect_ns'] + r['respond_ns'] for r in rows)
    from vanguard.common import Rejected
    def throttled(_):
        raise Rejected('Admission rate limit reached', 429)
    monkeypatch.setattr(lab['admission'], 'throttle', throttled)
    assert lab['app'].test_client().post('/api/challenge', json={}).status_code == 429
    assert len(timings(lab)) == 8  # No timing-log amplification after rate limiting.


def test_detection_stamp_precedes_policy_audit(lab, monkeypatch):
    import time
    register(lab)
    body = proof(lab)
    body['signature'] = 'aW52YWxpZA=='
    audit = lab['admission'].audit
    def delayed(event, name, detail):
        if event == 'rejected':
            time.sleep(0.02)
        return audit(event, name, detail)
    monkeypatch.setattr(lab['admission'], 'audit', delayed)
    assert lab['app'].test_client().post('/api/verify', json=body).status_code == 403
    row, = timings(lab)
    assert row['respond_ns'] >= 20_000_000
