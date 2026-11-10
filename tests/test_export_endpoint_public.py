import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from scripts import export_endpoint_public as exporter
from scripts.prepare_endpoint_pilot import prepare


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Export test root')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1)).sign(key, hashes.SHA256()))
    root = tmp_path / 'root.crt'
    root.write_bytes(cert.public_bytes(Encoding.PEM))
    public = tmp_path / 'public'
    profile = prepare(root, 'eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg=', public)
    data = {'ca': root.read_bytes(), 'server': profile['server_public_key'].encode(),
            'admin': json.dumps(profile).encode()}
    inventory = tmp_path / 'inventory.json'
    inventory.write_text(json.dumps({role: {'role': role} for role in data}))
    output = tmp_path / 'output'
    output.mkdir()
    monkeypatch.setattr(exporter, 'fetch', lambda node, command: data[node['role']])
    return inventory, output, data


def test_export_only_public_files_and_never_overwrites(inputs):
    inventory, output, data = inputs
    data['ca'] += b'\nTRAILING_NON_CERTIFICATE_DATA'
    first, profile = exporter.export(inventory, output)
    second, _ = exporter.export(inventory, output)
    assert first != second
    assert {p.name for p in first.iterdir()} == {'root.crt', 'profile.json', 'server-wg.pub'}
    assert 'TRAILING' not in (first / 'root.crt').read_text()
    assert json.loads((first / 'profile.json').read_text()) == profile
    assert first.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize('fault', ['profile', 'key', 'root_hash', 'certificate'])
def test_invalid_inputs_never_publish_output(inputs, fault):
    inventory, output, data = inputs
    if fault == 'profile':
        data['admin'] = b'{"schema":99}'
    elif fault == 'key':
        data['server'] = b'wrong-key'
    elif fault == 'certificate':
        data['ca'] = b'not a certificate'
    else:
        profile = json.loads(data['admin'])
        profile['root_sha256'] = '0' * 64
        data['admin'] = json.dumps(profile).encode()
    with pytest.raises(ValueError, match='tidak valid'):
        exporter.export(inventory, output)
    assert list(output.iterdir()) == []


def test_ssh_failure_never_publishes_or_exposes_stderr(inputs, monkeypatch):
    inventory, output, _ = inputs
    def fail(node, command):
        raise subprocess.CalledProcessError(255, 'ssh', stderr=b'PRIVATE_DETAIL')
    monkeypatch.setattr(exporter, 'fetch', fail)
    with pytest.raises(ValueError, match='SSH ca gagal') as error:
        exporter.export(inventory, output)
    assert 'PRIVATE_DETAIL' not in str(error.value)
    assert list(output.iterdir()) == []


def test_write_failure_removes_only_own_partial_folder(inputs, monkeypatch):
    inventory, output, _ = inputs
    existing = output / 'keep.txt'
    existing.write_text('keep')
    original = Path.write_bytes
    def fail(path, data):
        if path.name == 'profile.json':
            raise OSError('disk full')
        return original(path, data)
    monkeypatch.setattr(Path, 'write_bytes', fail)
    with pytest.raises(OSError):
        exporter.export(inventory, output)
    assert list(output.iterdir()) == [existing]
    assert existing.read_text() == 'keep'
