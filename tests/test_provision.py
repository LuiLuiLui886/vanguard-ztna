import json
from pathlib import Path

import pytest
from test_endpoint_profile import profile, public_bundle

from scripts.build_endpoint_package import provisioning_inputs
from vanguard.common import Rejected
from vanguard.onboarding import import_bundle
from vanguard.pki import fingerprint, load_cert
from vanguard.provision import load_provision, prepare


def inputs(lab, tmp_path):
    root = lab['ca'].path / 'root.crt'
    p = tmp_path / 'profile.json'
    data = profile(fingerprint(load_cert(root.read_bytes())))
    p.write_text(json.dumps(data))
    return dict(profile=p, root=root, device_id='vm-client', tunnel_ip='10.8.0.2',
                root_sha256=data['root_sha256'], server_public_key=data['server_public_key'])


def materialize(lab, tmp_path):
    result = provisioning_inputs(inputs(lab, tmp_path))
    package = tmp_path / 'public'
    package.mkdir()
    for name, value in result.items():
        (package / name).write_bytes(value)
    provision = load_provision(package / 'provision.json', package / 'profile.json', package / 'root.crt')
    return provision, package


def test_public_inputs_are_strict_and_strip_private_pem_tail(lab, tmp_path):
    value = inputs(lab, tmp_path)
    root = tmp_path / 'source.crt'
    root.write_bytes(Path(value['root']).read_bytes() + (lab['directory'] / 'identity.key').read_bytes())
    value['root'] = root
    generated = provisioning_inputs(value)
    assert set(generated) == {'root.crt', 'profile.json', 'provision.json'}
    assert all(b'PRIVATE KEY' not in x for x in generated.values())
    with pytest.raises(ValueError, match='explicit public'):
        provisioning_inputs(dict(value, password='must-not-be-bundled'))
    with pytest.raises(ValueError, match='trust pins'):
        provisioning_inputs(dict(value, root_sha256='0' * 64))


def test_resume_preserves_keys_session_and_public_request(lab, tmp_path):
    provision, _ = materialize(lab, tmp_path)
    directory = lab['directory']
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    export = tmp_path / 'export/request.json'
    first = prepare(directory, provision, export)
    assert first == prepare(directory, provision, export)
    assert all((directory / name).read_bytes() == value for name, value in before.items())
    assert set(json.loads(export.read_text())) == {'device_id', 'tunnel_ip', 'wg_public_key', 'csr'}
    assert not lab['wg'].active


def test_new_identity_is_local_and_waits_for_admin(lab, tmp_path):
    provision, _ = materialize(lab, tmp_path)
    directory = tmp_path / 'new-identity'
    export = tmp_path / 'export/request.json'
    assert prepare(directory, provision, export)['certificate_present'] is False
    before = (directory / 'identity.key').read_bytes(), (directory / 'wg.key').read_bytes()
    assert prepare(directory, provision, export)['certificate_present'] is False
    assert before == ((directory / 'identity.key').read_bytes(), (directory / 'wg.key').read_bytes())
    assert not lab['wg'].active


@pytest.mark.parametrize('conflict', ['allocation', 'partial', 'csr', 'wg', 'export'])
def test_conflicting_or_partial_identity_is_retained(lab, tmp_path, conflict):
    provision, _ = materialize(lab, tmp_path)
    directory = lab['directory']
    export = tmp_path / 'request.json'
    if conflict == 'allocation':
        provision['device_id'] = 'another-device'
    elif conflict == 'partial':
        (directory / 'request.json').unlink()
    elif conflict == 'csr':
        request = json.loads((directory / 'request.json').read_text())
        request['csr'] = 'invalid public CSR'
        (directory / 'request.json').write_text(json.dumps(request))
    elif conflict == 'wg':
        (directory / 'wg.key').write_text('A' * 43 + '=')
    else:
        export.write_text('{"different":true}')
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    with pytest.raises((Rejected, OSError, ValueError)):
        prepare(directory, provision, export)
    assert all((directory / name).read_bytes() == value for name, value in before.items())


def test_bundle_import_then_resume_creates_no_peer(lab, tmp_path):
    provision, _ = materialize(lab, tmp_path)
    bundle, root, p = public_bundle(lab, tmp_path)
    directory = lab['directory']
    (directory / 'device.crt').unlink()
    before = (directory / 'identity.key').read_bytes()
    export = tmp_path / 'request.json'
    assert prepare(directory, provision, export)['certificate_present'] is False
    import_bundle(directory, bundle, root, p)
    assert prepare(directory, provision, export)['certificate_present'] is True
    assert (directory / 'identity.key').read_bytes() == before
    assert not lab['wg'].active


@pytest.mark.parametrize('change', [{'schema': True}, {'token': 'unexpected'}, {'root_sha256': 'a' * 64}])
def test_contract_rejects_unknown_fields_or_wrong_pins(lab, tmp_path, change):
    _, package = materialize(lab, tmp_path)
    p = package / 'provision.json'
    p.write_text(json.dumps(dict(json.loads(p.read_text()), **change)))
    with pytest.raises(Rejected):
        load_provision(p, package / 'profile.json', package / 'root.crt')
