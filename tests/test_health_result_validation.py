import json
import sys

import pytest

from vanguard import health
from vanguard.common import make_app


@pytest.mark.parametrize('value', [
    None, [], 'unexpected', 1,
    {'status': 'ready'}, {'status': 'ready', 'checks': {}},
    {'status': 'ready', 'checks': {'ca_state': 'unknown'}},
    {'status': 'ready', 'checks': {'ca_state': True}},
    {'status': 'not_ready', 'checks': {'ca_state': 'ready'}},
])
def test_invalid_child_json_never_crashes_or_reports_healthy(tmp_path, monkeypatch, value):
    worker = tmp_path / 'probe-output'
    worker.write_text(f'#!{sys.executable}\nprint({json.dumps(value)!r})\n')
    worker.chmod(0o700)
    monkeypatch.setattr(health.sys, 'executable', str(worker))
    app = make_app('vanguard.ca')
    app.config['TESTING'] = True
    response = app.test_client().get('/readyz')
    assert response.status_code == 503
    assert response.json == {'status': 'not_ready', 'checks': {'probe': 'unknown'}}
    diagnostic = health.bounded_readiness('ca', diagnostics=True)
    assert diagnostic['diagnostics']['probe']['reason'] == 'invalid_result'


@pytest.mark.parametrize('value', [
    None, [], {'status': 'ready'},
    {'status': 'ready', 'checks': {'ca_state': 'unknown'}},
])
def test_malformed_dependency_cannot_be_ready(monkeypatch, value):
    class Response:
        status_code = 200

        def json(self):
            return value

    monkeypatch.setattr(health.requests, 'get', lambda *a, **kw: Response())
    with pytest.raises(ValueError, match='Invalid readiness response'):
        health.dependency_ready('https://example.invalid', '/unused/root.crt')
