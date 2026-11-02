import json
import time

import pytest

from vanguard import client
from vanguard.common import Rejected


def session(**changes):
    return {'username': 'test-user', 'session_token': 'test-session-' + 'a' * 32,
            'expires_at': time.time() + 60, **changes}


class Response:
    def __init__(self, value):
        self.value = value

    def call(self, method, endpoint, body):
        return self.value


@pytest.mark.parametrize('response', [
    None, [], 'unexpected', {},
    {'username': 'test-user', 'expires_at': 1},
    session(username='different-user'),
    session(session_token=None), session(session_token='short'),
    session(expires_at='tomorrow'), session(expires_at=True),
    session(expires_at=0), session(expires_at=float('nan')),
    session(expires_at=float('inf')),
])
def test_invalid_login_response_preserves_existing_session(tmp_path, response):
    directory = tmp_path / 'client'
    directory.mkdir()
    target = directory / 'employee-session.json'
    original = json.dumps(session()).encode()
    target.write_bytes(original)
    try:
        with pytest.raises(Rejected, match='Unexpected employee login response'):
            client.login_employee(directory, Response(response), 'test-user', 'test-password')
    finally:
        assert target.read_bytes() == original
        assert {p.name for p in directory.iterdir()} == {'employee-session.json', '.session.lock'}


def test_login_persists_only_session_fields(tmp_path):
    response = session(password='secret-response-sentinel', arbitrary={'raw': 'response-body'})
    client.login_employee(tmp_path, Response(response), 'test-user', 'test-password')
    stored = json.loads((tmp_path / 'employee-session.json').read_text())
    assert stored == {k: response[k] for k in ('username', 'session_token', 'expires_at')}
    assert 'secret-response-sentinel' not in (tmp_path / 'employee-session.json').read_text()


@pytest.mark.parametrize('response', [None, [], 'unexpected',
                                     {'revoked': True, 'peer_removal_confirmed': False}])
def test_bad_logout_confirmation_keeps_token_and_supports_retry(tmp_path, response):
    target = tmp_path / 'employee-session.json'
    original = json.dumps(session()).encode()
    target.write_bytes(original)
    with pytest.raises(Rejected, match='Pencabutan server belum terkonfirmasi'):
        client.logout_employee(tmp_path, Response(response))
    assert target.read_bytes() == original
    result = client.logout_employee(tmp_path, Response({'revoked': True,
                                                       'peer_removal_confirmed': True}))
    assert result['revoked']
    assert not target.exists()
