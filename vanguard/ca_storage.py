"""Linux CA write-ahead publication. Caller holds the CA lock throughout.

OpenSSL only edits a private working copy. A durable manifest is the commit
decision; recovery always finishes that decision, never restores an older CA.
Readers must hold the same lock and recover before inspecting published state.
"""

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

from .common import Rejected, private_dir

FILES = ('openssl.cnf', 'root.crt', 'index.txt', 'index.txt.attr', 'serial',
         'crlnumber', 'crl.pem', 'index.txt.old', 'index.txt.attr.old',
         'serial.old', 'crlnumber.old')
DIRECTORIES = ('private', 'newcerts', 'issued', 'tls-issued')


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_write(path, data):
    temporary = path.with_name('.' + path.name + '.publishing')
    with open(temporary, 'wb') as out:
        os.chmod(temporary, 0o600)
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, path)
    sync_dir(path.parent)


class Publication:
    def __init__(self, root):
        self.root = Path(root)
        self.journal = self.root / '.transaction'
        self.work = self.journal / ('work-' + uuid.uuid4().hex)
        self.commit = self.journal / 'commit.json'
        self.completed = self.journal / 'completed'

    def recover(self):
        if not self.commit.exists():
            return
        try:
            decision = json.loads(self.commit.read_text())
            generation = decision['work']
            if not isinstance(generation, str) or not generation.startswith('work-') or '/' in generation:
                raise ValueError()
            self.work = self.journal / generation
            if self.work.is_symlink():
                raise ValueError()
            manifest = decision['files']
            if not isinstance(manifest, dict) or not manifest:
                raise ValueError()
            required = {'openssl.cnf', 'root.crt', 'private/root.key', 'index.txt',
                        'index.txt.attr', 'serial', 'crlnumber', 'crl.pem'}
            if not required <= manifest.keys():
                raise ValueError()
            # Verify the whole committed generation before publishing any file.
            for name, digest in manifest.items():
                relative = Path(name)
                if (relative.is_absolute() or '..' in relative.parts
                        or not (name in FILES or
                                len(relative.parts) == 2 and relative.parts[0] in DIRECTORIES)):
                    raise ValueError()
                source = self.work / name
                if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                    raise ValueError()
            for name in sorted(manifest):
                target = self.root / name
                private_dir(target.parent)
                if target.is_symlink():
                    raise ValueError()
                self.publish_file(name)
            for name in DIRECTORIES:
                private_dir(self.root / name)
            sync_dir(self.root)
            # All members durable before removing the commit decision. A crash
            # before durable removal merely replays the identical generation.
            self.commit.unlink()
            sync_dir(self.journal)
            durable_write(self.completed, b'publication complete\n')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise Rejected('CA committed transaction needs operator inspection', 503) from exc

    def publish_file(self, name):
        durable_write(self.root / name, (self.work / name).read_bytes())

    def prepare(self):
        self.recover()
        if self.journal.exists():
            if self.completed.exists():
                shutil.rmtree(self.journal)
            else:
                # No commit decision: retain interrupted OpenSSL evidence.
                # It is never used to restore or guess published state.
                archive = private_dir(self.root / 'interrupted-transactions')
                os.rename(self.journal, archive / uuid.uuid4().hex)
                sync_dir(archive)
            sync_dir(self.root)
        # Never reuse an old OpenSSL working pathname: a child surviving its
        # parent must not be able to write into the next transaction.
        self.work = self.journal / ('work-' + uuid.uuid4().hex)
        private_dir(self.work)
        sync_dir(self.root)
        for name in FILES:
            source = self.root / name
            if source.exists():
                shutil.copyfile(source, self.work / name)
                os.chmod(self.work / name, 0o600)
        for name in DIRECTORIES:
            source = self.root / name
            if source.exists():
                shutil.copytree(source, self.work / name)
        return self.work

    def seal(self):
        manifest = {}
        for path in sorted(self.work.rglob('*')):
            if path.is_file() and path.name != 'ca.lock':
                name = str(path.relative_to(self.work))
                if name not in FILES and path.relative_to(self.work).parts[0] not in DIRECTORIES:
                    continue
                os.chmod(path, 0o600)
                with open(path, 'rb') as stream:
                    os.fsync(stream.fileno())
                manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(self.work.rglob('*'), reverse=True):
            if path.is_dir():
                sync_dir(path)
        sync_dir(self.work)
        sync_dir(self.journal)
        durable_write(self.commit, json.dumps({'work': self.work.name, 'files': manifest},
                                             sort_keys=True).encode())
        self.recover()
