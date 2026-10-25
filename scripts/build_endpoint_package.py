#!/usr/bin/env python3
"""Build an unsigned offline candidate from an explicitly supplied Windows wheelhouse."""

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]


def runtime_inputs(directory, lock):
    if directory is None:
        raise ValueError('Runtime directory required for complete offline package')
    directory = Path(directory)
    result = {}
    for role in ('python', 'wireguard'):
        item = lock[role]
        name = item['file']
        if not re.fullmatch(r'runtimes/[a-zA-Z0-9_.-]+', name):
            raise ValueError('Invalid runtime path')
        path = directory / Path(name).name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing runtime: ' + role)
        if path.stat().st_size != item['size'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Runtime integrity mismatch: ' + role)
        result[name] = path
    return result


def build(wheelhouse, output, runtime_directory=None):
    wheelhouse, output = Path(wheelhouse), Path(output)
    if output.exists():
        raise ValueError('Output exists; preserve prior package evidence')
    pins = {}
    for line in (ROOT / 'deploy/constraints.txt').read_text().splitlines():
        name, version = line.split('==')
        if name not in ('gunicorn',):
            pins[canonicalize_name(name)] = version
    pins['colorama'] = '0.4.6'
    pins['pywin32'] = '312'  # matches the previously verified Windows lab wheelhouse
    version = re.search(r'^version = "([^"]+)"', (ROOT / 'pyproject.toml').read_text(), re.M)[1]
    pins['vanguard-ztna'] = version
    supported = set(cpython_tags((3, 13), platforms=['win_amd64']))
    supported.update(compatible_tags((3, 13), interpreter='cp313', platforms=['win_amd64']))
    selected = {}
    metadata = {}
    for path in wheelhouse.glob('*.whl'):
        name, wheel_version, _, tags = parse_wheel_filename(path.name)
        if name in pins and str(wheel_version) == pins[name] and tags & supported:
            if name in selected:
                raise ValueError('Ambiguous compatible wheel: ' + name)
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                meta = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
                if len(meta) != 1:
                    raise ValueError('Invalid wheel metadata')
                parsed = BytesParser().parsebytes(archive.read(meta[0]))
                if canonicalize_name(parsed['Name']) != name or parsed['Version'] != pins[name]:
                    raise ValueError('Wheel metadata mismatch')
            selected[name] = path
            metadata[name] = parsed
    missing = sorted(set(pins) - selected.keys())
    if missing:
        raise ValueError('Missing pinned Windows wheels: ' + ', '.join(missing))
    environment = default_environment()
    environment.update(sys_platform='win32', os_name='nt', platform_system='Windows',
                       platform_machine='AMD64', python_version='3.13', python_full_version='3.13.16',
                       implementation_name='cpython', extra='')
    for name, meta in metadata.items():
        if '3.13.16' not in SpecifierSet(meta.get('Requires-Python', '')):
            raise ValueError('Runtime incompatible with ' + name)
        for text in meta.get_all('Requires-Dist', []):
            requirement = Requirement(text)
            if requirement.marker is not None and not requirement.marker.evaluate(environment):
                continue
            key = canonicalize_name(requirement.name)
            if key not in pins or pins[key] not in requirement.specifier:
                raise ValueError('Unresolved Windows dependency: ' + str(requirement))
    runtime_lock = json.loads((ROOT / 'deploy/endpoint/windows/runtime-lock.json').read_text())
    runtimes = runtime_inputs(runtime_directory, runtime_lock)
    output.mkdir(parents=True)
    (output / 'runtimes').mkdir()
    for name, path in runtimes.items():
        shutil.copyfile(path, output / name)
    (output / 'wheels').mkdir()
    lines = []
    for name, path in sorted(selected.items()):
        shutil.copyfile(path, output / 'wheels' / path.name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f'{name}=={pins[name]} --hash=sha256:{digest}')
    for path in sorted((ROOT / 'deploy/endpoint/windows').iterdir()):
        if path.is_file():
            shutil.copyfile(path, output / path.name)
    # One authoritative manual; package contains a generated offline HTML copy.
    manual = (ROOT / 'docs/MODUL_PENGGUNAAN_VANGUARD.html').read_text()
    def published_link(match):
        link = match[1]
        if link.startswith(('#', 'https://', 'http://', 'mailto:')):
            return match[0]
        from posixpath import normpath
        target = normpath('docs/' + link)
        return 'href="https://github.com/LuiLuiLui886/vanguard-ztna/blob/main/' + target + '"'
    manual = re.sub(r'href="([^"]+)"', published_link, manual)
    (output / 'MODUL_PENGGUNAAN_VANGUARD.html').write_text(manual)
    (output / 'README.md').write_text('# VanGuard Windows10/11 x64\n\n'
        'Buka MODUL_PENGGUNAAN_VANGUARD.html; Bab10 untuk instalasi dan Bab11–12 untuk endpoint.\n'
        'Manual ini berasal dari satu sumber resmi repository. Hasil native ada pada checkpoint.\n')
    (output / 'requirements.lock').write_text('\n'.join(lines) + '\n')
    hashes = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = {'schema': 1, 'version': version, 'target': 'cp313-win_amd64', 'signed': False,
                'status': 'CANDIDATE_NATIVE_TESTS_REQUIRED', 'files': hashes}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def verify_package(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'manifest.json'}:
        raise ValueError('Unexpected/missing package members')
    for name, digest in manifest['files'].items():
        path = directory / name
        if (not re.fullmatch(r'(?:(?:wheels|runtimes)/)?[a-zA-Z0-9_.-]+', name) or path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
            raise ValueError('Package integrity mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheelhouse', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-directory', type=Path, required=True)
    args = parser.parse_args()
    build(args.wheelhouse, args.output, args.runtime_directory)
    result = verify_package(args.output)
    print(json.dumps({'status': result['status'], 'files': len(result['files']), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
