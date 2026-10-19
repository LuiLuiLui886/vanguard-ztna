import json
from types import SimpleNamespace

import pytest
from conftest import register

from deploy.firewall import rules
from vanguard.client import admit
from vanguard.common import Rejected
from vanguard.resource_policy import RESOURCE, NftResources, load_policy


def test_default_deny_and_exact_policy_schema(tmp_path):
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps({'grants': []}))
    assert load_policy(path) == set()
    for changed in ({'port': 22}, {'protocol': 'udp'}, {'address': '192.168.100.20'},
                    {'resource': '*'}, {'username': '*'}):
        path.write_text(json.dumps({'grants': [{**RESOURCE, 'device_id': 'vm-client',
                                             'username': 'employee-test', **changed}]}))
        with pytest.raises(Rejected):
            load_policy(path)


def test_application_policy_uses_session_identity_and_scoped_logout(lab, tmp_path, monkeypatch):
    from vanguard import resource_policy
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps({'grants': [{**RESOURCE, 'device_id': 'vm-client',
                                         'username': 'employee-test'}]}))
    commands = []
    def execute(args, **kw):
        commands.append(kw['input'].decode())
        return SimpleNamespace(stdout=b'')
    monkeypatch.setattr(resource_policy, 'run', execute)
    lab['admission'].resources = NftResources(path)
    register(lab)
    assert commands == []
    admit(lab['directory'], lab['remote'])
    assert '10.8.0.2 . 10.8.0.1 . tcp . 8082 timeout' in commands[-1]
    lab['admission'].logout_employee(lab['employee_session'])
    assert commands[-1] == 'flush set inet vanguard application_access\n'
    assert not lab['wg'].active


def test_firewall_checks_application_before_established_and_guards_output():
    content = rules('server', '192.168.100.1', True, True)
    assert content.index('tcp dport 8082 jump') < content.index('ct state established')
    assert 'flags timeout' in content and 'tcp sport 8082 counter drop' in content
    assert 'ip daddr 10.8.0.0/24 iifname != "wg0" counter drop' in content
