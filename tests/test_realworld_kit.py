import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

sys.path.insert(0, str(Path('scripts').resolve()))
import build_realworld_kit as kit  # noqa: E402
import pilot_preflight as preflight  # noqa: E402
from prepare_endpoint_pilot import prepare  # noqa: E402

spec = importlib.util.spec_from_file_location('verify_kit', 'deploy/pilot/verify_kit.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_host_preflight_never_confuses_power_or_flag_with_readiness():
    addresses = [{'ifname': 'enp2s0', 'operstate': 'UP', 'addr_info': [
        {'local': '192.168.50.10', 'prefixlen': 24}]},
        {'ifname': 'virbr-vg', 'addr_info': [{'local': '192.168.100.1', 'prefixlen': 24}]}]
    nodes = {name: 'running' if name in preflight.SERVICES else 'shut off' for name in preflight.NODES}
    report = preflight.assess(addresses, '1', nodes)
    assert report['status'] == 'MANUAL_REVIEW_REQUIRED'
    assert report['ready_for_production'] is False and report['mutations'] is False
    assert {c['status'] for c in report['checks']} == {'PASS', 'MANUAL', 'NOT_TESTED'}
    nodes['VM-CA'] = 'shut off'
    assert preflight.assess(addresses, '1', nodes)['status'] == 'BLOCKED'
    addresses[0]['operstate'] = 'DOWN'
    assert preflight.assess(addresses, '1', nodes)['checks'][0]['status'] == 'FAIL'


def test_host_inspection_failures_remain_unknown():
    report = preflight.assess(None, None, {})
    assert report['status'] == 'BLOCKED'
    assert all(c['status'] == 'UNKNOWN' for c in report['checks'][:9])


@pytest.fixture
def public_inputs(tmp_path):
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Kit test root')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(1).not_valid_before(now)
            .not_valid_after(now + timedelta(days=1)).sign(key, hashes.SHA256()))
    root = tmp_path / 'root.crt'
    root.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    import base64
    public = tmp_path / 'public'
    prepare(root, base64.b64encode(b'x' * 32).decode(), public)
    endpoint = tmp_path / 'endpoint'
    (endpoint / 'wheels').mkdir(parents=True)
    wheel = endpoint / 'wheels/vanguard_ztna-0.1.12-py3-none-any.whl'
    wheel.write_bytes(b'synthetic fixture; actual wheel verified separately')
    manifest = {'schema': 1, 'version': '0.1.12', 'target': 'cp313-win_amd64',
                'files': {'wheels/' + wheel.name: hashlib.sha256(wheel.read_bytes()).hexdigest()}}
    raw = (json.dumps(manifest) + '\n').encode()
    (endpoint / 'manifest.json').write_bytes(raw)
    return endpoint, public, wheel, hashlib.sha256(raw).hexdigest()


def test_kit_copies_only_public_config_and_detects_tamper(public_inputs, tmp_path):
    endpoint, public, wheel, digest = public_inputs
    (public / 'private.key').write_text('DO_NOT_COPY')
    (public / 'admin-public.env').write_text('DO_NOT_COPY_TOKEN')
    output = tmp_path / 'kit'
    result = kit.build(endpoint, public, wheel, output, digest)
    assert not list(output.rglob('private.key'))
    assert 'DO_NOT_COPY' not in (output / 'config/admin-public.env').read_text()
    assert result['ready_for_production'] is False
    manifest_hash = hashlib.sha256((output / 'kit-manifest.json').read_bytes()).hexdigest()
    assert verifier.verify(output, manifest_hash) == len(result['files'])
    with pytest.raises(ValueError, match='Output exists'):
        kit.build(endpoint, public, wheel, output, digest)
    (output / 'config/profile.json').write_text('{}')
    with pytest.raises(ValueError, match='hash mismatch'):
        verifier.verify(output, manifest_hash)


def test_kit_rejects_untrusted_or_mismatched_application(public_inputs, tmp_path):
    endpoint, public, wheel, digest = public_inputs
    output = tmp_path / 'kit'
    with pytest.raises(ValueError, match='fingerprint'):
        kit.build(endpoint, public, wheel, output, '0' * 64)
    assert not output.exists()
    different = tmp_path / wheel.name
    different.write_bytes(b'wrong version/source')
    with pytest.raises(ValueError, match='Backend wheel'):
        kit.build(endpoint, public, different, output, digest)
    assert not output.exists()


def test_verifier_rejects_extra_member_and_untrusted_manifest(public_inputs, tmp_path):
    endpoint, public, wheel, digest = public_inputs
    output = tmp_path / 'kit'
    kit.build(endpoint, public, wheel, output, digest)
    expected = hashlib.sha256((output / 'kit-manifest.json').read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='independently trusted'):
        verifier.verify(output, '0' * 64)
    (output / 'extra.ps1').write_text('unapproved')
    with pytest.raises(ValueError, match='Unexpected'):
        verifier.verify(output, expected)


def test_verifier_rejects_symlink(public_inputs, tmp_path):
    endpoint, public, wheel, digest = public_inputs
    output = tmp_path / 'kit'
    kit.build(endpoint, public, wheel, output, digest)
    expected = hashlib.sha256((output / 'kit-manifest.json').read_bytes()).hexdigest()
    (output / 'link').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symbolic'):
        verifier.verify(output, expected)
