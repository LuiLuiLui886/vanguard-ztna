"""Private generations must be fully durable before their commit is published."""

import multiprocessing
import os
import signal
import threading

import pytest

from vanguard.ca import Authority
from vanguard import ca_storage


def test_commit_waits_for_every_file_flush(tmp_path, monkeypatch):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    reached, release = threading.Event(), threading.Event()
    original = ca_storage.sync_generation
    errors = []

    def sync(directory, members):
        reached.set()
        assert release.wait(10)
        original(directory, members)

    def refresh():
        try:
            ca.crl()
        except BaseException as exc:
            errors.append(exc)

    with monkeypatch.context() as patch:
        patch.setattr(ca_storage, 'sync_generation', sync)
        worker = threading.Thread(target=refresh)
        worker.start()
        try:
            assert reached.wait(10)
            assert not (ca.path / '.transaction/commit.json').exists()
        finally:
            release.set()
            worker.join(20)
        assert not worker.is_alive()
        assert not errors
    ca.check_state()


def test_failed_generation_flush_keeps_old_state_and_evidence(tmp_path, monkeypatch):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    names = ('root.crt', 'private/root.key', 'index.txt', 'serial', 'crlnumber', 'crl.pem')
    before = {name: (ca.path / name).read_bytes() for name in names}

    def fail(directory, members):
        raise OSError('injected generation flush failure')

    with monkeypatch.context() as patch:
        patch.setattr(ca_storage, 'sync_generation', fail)
        with pytest.raises(OSError, match='injected'):
            ca.crl()
    assert all((ca.path / name).read_bytes() == data for name, data in before.items())
    assert not (ca.path / '.transaction/commit.json').exists()
    ca.crl()
    ca.check_state()
    archives = list((ca.path / 'interrupted-transactions').iterdir())
    assert len(archives) == 1
    assert list(archives[0].glob('work-*/root.crt'))


def test_process_killed_during_file_flush_never_commits_partial_generation(tmp_path):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    names = ('index.txt', 'serial', 'crlnumber', 'crl.pem', 'private/root.key')
    before = {name: (ca.path / name).read_bytes() for name in names}

    def interrupted():
        def kill(directory, members):
            os.kill(os.getpid(), signal.SIGKILL)

        ca_storage.sync_generation = kill
        ca.crl()

    process = multiprocessing.get_context('fork').Process(target=interrupted)
    process.start()
    process.join(20)
    assert process.exitcode == -signal.SIGKILL
    assert all((ca.path / name).read_bytes() == data for name, data in before.items())
    assert not (ca.path / '.transaction/commit.json').exists()
    ca.crl()
    ca.check_state()
    assert list((ca.path / 'interrupted-transactions').glob('*/work-*/crlnumber'))


@pytest.mark.parametrize('error', [5, 28])
def test_syncfs_error_aborts_before_commit(tmp_path, monkeypatch, error):
    import ctypes
    from types import SimpleNamespace

    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    before = (ca.path / 'crlnumber').read_bytes()

    def fail(fd):
        ctypes.set_errno(error)
        return -1

    monkeypatch.setattr(ca_storage.sys, 'platform', 'linux')
    monkeypatch.setattr(ca_storage.os, 'uname', lambda: SimpleNamespace(release='5.15.0-test'))
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: SimpleNamespace(syncfs=fail))
    with pytest.raises(OSError) as failure:
        ca.crl()
    assert failure.value.errno == error
    assert not (ca.path / '.transaction/commit.json').exists()
    assert (ca.path / 'crlnumber').read_bytes() == before


def test_old_kernel_fallback_syncs_every_member(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from pathlib import Path

    members = [tmp_path / 'a', tmp_path / 'b']
    for p in members:
        p.write_bytes(b'private generation fixture')
    seen = set()
    original = os.fsync

    def sync(fd):
        seen.add(Path(os.readlink(f'/proc/self/fd/{fd}')))
        original(fd)

    monkeypatch.setattr(ca_storage.os, 'uname', lambda: SimpleNamespace(release='5.4.0-test'))
    monkeypatch.setattr(os, 'fsync', sync)
    ca_storage.sync_generation(tmp_path, members)
    assert seen == set(members)


def test_syncfs_rejects_member_on_another_filesystem(tmp_path, monkeypatch):
    import ctypes
    from types import SimpleNamespace

    def unexpected(fd):
        raise AssertionError('Must reject before syncing the wrong filesystem')

    monkeypatch.setattr(ca_storage.os, 'uname', lambda: SimpleNamespace(release='5.15.0-test'))
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: SimpleNamespace(syncfs=unexpected))
    member = SimpleNamespace(stat=lambda: SimpleNamespace(st_dev=tmp_path.stat().st_dev + 1))
    with pytest.raises(OSError, match='crosses filesystems'):
        ca_storage.sync_generation(tmp_path, [member])
