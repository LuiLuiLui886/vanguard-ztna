#!/usr/bin/env python3
"""Verify every kit member against an independently trusted manifest fingerprint."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(directory, expected_sha256):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError('Kit root cannot be a symbolic link')
    manifest_path = directory / 'kit-manifest.json'
    if manifest_path.is_symlink():
        raise ValueError('Manifest cannot be a symbolic link')
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256.lower():
        raise ValueError('Manifest differs from independently trusted fingerprint')
    manifest = json.loads(raw)
    if manifest['schema'] != 1 or manifest['ready_for_production'] is not False:
        raise ValueError('Invalid candidate manifest')
    actual = set()
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symbolic links are not permitted')
        if path.is_file():
            actual.add(path.relative_to(directory).as_posix())
    if actual != set(manifest['files']) | {'kit-manifest.json'}:
        raise ValueError('Unexpected or missing kit member')
    for name, digest in manifest['files'].items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe member path')
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Kit member hash mismatch: ' + name)
    return len(manifest['files'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expected-manifest-sha256', required=True)
    args = parser.parse_args()
    count = verify(args.directory, args.expected_manifest_sha256)
    print(f'Integrity PASS: {count} members. Native installation/network readiness remains unverified.')


if __name__ == '__main__':
    main()
