"""Avoid rewriting identical published members without weakening durability."""

import json
import os
from pathlib import Path

import pytest

from vanguard.ca_storage import Publication
from vanguard.common import Rejected, locked


def test_crl_refresh_keeps_identical_published_files_and_syncs_them(lab, monkeypatch):
    ca = lab['ca']
    paths = [ca.path / name for name in ('root.crt', 'private/root.key', 'index.txt', 'serial')]
    paths += list((ca.path / 'newcerts').glob('*.pem'))
    before = {p: (p.stat().st_ino, p.read_bytes()) for p in paths}
    number = int((ca.path / 'crlnumber').read_text(), 16)
    synced = set()
    original = os.fsync

    def sync(fd):
        synced.add(Path(os.readlink(f'/proc/self/fd/{fd}')))
        original(fd)

    monkeypatch.setattr(os, 'fsync', sync)
    ca.crl()
    ca.check_state()
    assert int((ca.path / 'crlnumber').read_text(), 16) > number
    assert all((p.stat().st_ino, p.read_bytes()) == value for p, value in before.items())
    assert set(paths) <= synced
    assert {p.parent for p in paths} <= synced


def test_sync_failure_on_identical_member_preserves_commit_for_roll_forward(lab, monkeypatch):
    ca = lab['ca']
    original = os.fsync

    def fail(fd):
        if Path(os.readlink(f'/proc/self/fd/{fd}')) == ca.path / 'root.crt':
            raise OSError('injected durability failure')
        original(fd)

    with monkeypatch.context() as patch:
        patch.setattr(os, 'fsync', fail)
        with pytest.raises(Rejected, match='operator inspection'):
            ca.crl()
    manifest = ca.path / '.transaction/commit.json'
    decision = json.loads(manifest.read_text())
    work = ca.path / '.transaction' / decision['work']
    expected = {name: (work / name).read_bytes() for name in decision['files']}
    with locked(ca.lock):
        Publication(ca.path).recover()
        ca.check_state()
    assert not manifest.exists()
    assert all((ca.path / name).read_bytes() == content for name, content in expected.items())


def test_identical_member_permissions_are_repaired_before_commit(lab):
    ca = lab['ca']
    key = ca.path / 'private/root.key'
    inode = key.stat().st_ino
    key.chmod(0o644)
    ca.crl()
    assert key.stat().st_mode & 0o777 == 0o600
    assert key.stat().st_ino == inode
    ca.check_state()


def test_directory_sync_failure_retains_entire_committed_generation(lab, monkeypatch):
    from vanguard import ca_storage

    ca = lab['ca']
    manifest = ca.path / '.transaction/commit.json'
    original = ca_storage.sync_dir

    def fail(path):
        if path == ca.path / 'newcerts' and manifest.exists():
            raise OSError('injected directory durability failure')
        original(path)

    with monkeypatch.context() as patch:
        patch.setattr(ca_storage, 'sync_dir', fail)
        with pytest.raises(Rejected, match='operator inspection'):
            ca.crl()
    decision = json.loads(manifest.read_text())
    expected = {name: (ca.path / '.transaction' / decision['work'] / name).read_bytes()
                for name in decision['files']}
    # Simulate loss of one unsynced rename, while the durable work still exists.
    (ca.path / 'crl.pem').unlink()
    with locked(ca.lock):
        Publication(ca.path).recover()
        ca.check_state()
    assert not manifest.exists()
    assert all((ca.path / name).read_bytes() == data for name, data in expected.items())


def test_parent_barriers_are_bounded_by_directories_not_certificate_count(lab, monkeypatch):
    from collections import Counter

    from vanguard import ca_storage

    ca = lab['ca']
    parents = {ca.path, *(ca.path / name for name in ca_storage.DIRECTORIES)}
    seen = Counter()
    original = ca_storage.sync_dir

    def sync(path):
        if path in parents and (ca.path / '.transaction/commit.json').exists():
            seen[path] += 1
        original(path)

    monkeypatch.setattr(ca_storage, 'sync_dir', sync)
    ca.crl()
    ca.check_state()
    assert set(seen) == parents
    assert all(count == 1 for count in seen.values())
