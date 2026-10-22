import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('endpoint_package', 'scripts/build_endpoint_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def test_missing_windows_wheels_fail_before_output(tmp_path):
    source = tmp_path / 'wheels'
    source.mkdir()
    target = tmp_path / 'package'
    with pytest.raises(ValueError, match='Missing pinned'):
        package.build(source, target)
    assert not target.exists()


def test_package_hashes_and_exact_members_are_required(tmp_path):
    file = tmp_path / 'Install-VanGuard.ps1'
    file.write_text('synthetic test payload')
    manifest = {'files': {file.name: hashlib.sha256(file.read_bytes()).hexdigest()}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    assert package.verify_package(tmp_path) == manifest
    file.write_text('tampered payload')
    with pytest.raises(ValueError, match='integrity'):
        package.verify_package(tmp_path)
    file.write_text('synthetic test payload')
    (tmp_path / 'extra.ps1').write_text('unexpected')
    with pytest.raises(ValueError, match='members'):
        package.verify_package(tmp_path)


def test_manifest_cannot_reference_outside_package(tmp_path):
    (tmp_path / 'manifest.json').write_text(json.dumps({'files': {'../other': 'a'*64}}))
    with pytest.raises(ValueError):
        package.verify_package(tmp_path)


def test_windows_entrypoints_do_not_reuse_vm_provisioning():
    # Supplementary source guard, explicitly NOT a native Windows execution test.
    root = Path('deploy/endpoint/windows')
    source = '\n'.join(p.read_text() for p in root.glob('*.ps1'))
    for forbidden in ('Set-NetIPAddress', 'New-NetIPAddress', 'Set-DnsClientServerAddress',
                      'Set-ExecutionPolicy', 'Invoke-Expression', 'Stop-Process',
                      'bootstrap.ps1', 'AutoAdminLogon', 'Restart-Computer'):
        assert forbidden not in source
    assert '--no-index' in source and '--require-hashes' in source
    assert "$setup.status -ne 'INSTALLED'" in source
    assert '$setup.release -ne $state.release' in source
    assert "'S-1-5-80-*'" not in source
    assert 'NT SERVICE\\TrustedInstaller' in source
    assert 'Marker kepemilikan berbeda' in source
