"""Real OpenSSL in temporary CAs; child process death, never a production CA."""

import json
import multiprocessing
import os
import signal

import pytest

from vanguard.ca import Authority
from vanguard.ca_storage import Publication
from vanguard.client import initialize


def test_issue_interruption_does_not_create_second_certificate(tmp_path):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    request = json.loads(initialize(tmp_path / 'client', 'crash-test').read_text())

    def interrupted():
        original = Authority.openssl

        def stop_after_sign(self, *args):
            result = original(self, *args)
            if '-in' in args:
                os.kill(os.getpid(), signal.SIGKILL)
            return result

        Authority.openssl = stop_after_sign
        ca.issue('crash-test', request['csr'])

    process = multiprocessing.get_context('fork').Process(target=interrupted)
    process.start()
    process.join(20)
    assert process.exitcode == -signal.SIGKILL
    result = ca.issue('crash-test', request['csr'])
    assert ca.issue('crash-test', request['csr']) == result
    assert len((ca.path / 'index.txt').read_text().splitlines()) == 1


@pytest.mark.parametrize('name', ['serial', 'crlnumber'])
def test_damaged_counter_is_not_guessed(tmp_path, name):
    from vanguard.common import Rejected

    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    (ca.path / name).write_text('')
    before = (ca.path / 'index.txt').read_bytes()
    with pytest.raises(Rejected):
        ca.crl()
    assert (ca.path / name).read_text() == ''
    assert (ca.path / 'index.txt').read_bytes() == before


@pytest.mark.parametrize('operation', ['issue', 'revoke', 'crl'])
@pytest.mark.parametrize('boundary', ['crlnumber', 'index.txt', 'serial'])
def test_kill_during_publication_rolls_forward_entire_state(tmp_path, operation, boundary):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    request = json.loads(initialize(tmp_path / 'client', 'crash-test').read_text())
    old = ca.issue('crash-test', request['csr'])
    ca.revoke(old['serial'])
    request2 = json.loads(initialize(tmp_path / 'client2', 'second-test', '10.8.0.3').read_text())
    second = ca.issue('second-test', request2['csr']) if operation == 'revoke' else None
    root_before = (ca.path / 'private/root.key').read_bytes()

    def interrupted():
        original = Publication.publish_file

        def publish_and_die(self, name):
            original(self, name)
            if name == boundary:
                os.kill(os.getpid(), signal.SIGKILL)

        Publication.publish_file = publish_and_die
        if operation == 'issue':
            ca.issue('second-test', request2['csr'])
        elif operation == 'revoke':
            ca.revoke(second['serial'])
        else:
            ca.crl()

    process = multiprocessing.get_context('fork').Process(target=interrupted)
    process.start()
    process.join(20)
    assert process.exitcode == -signal.SIGKILL
    assert (ca.path / '.transaction/commit.json').exists()
    # A fresh process/instance finishes the exact signed generation first.
    fresh = Authority(ca.path)
    fresh.crl()
    fresh.check_state()
    from cryptography import x509
    crl = x509.load_pem_x509_crl((ca.path / 'crl.pem').read_bytes())
    assert crl.get_revoked_certificate_by_serial_number(int(old['serial'], 16))
    if operation == 'revoke':
        assert crl.get_revoked_certificate_by_serial_number(int(second['serial'], 16))
    if operation == 'issue':
        fresh.issue('second-test', request2['csr'])
        assert len((ca.path / 'index.txt').read_text().splitlines()) == 2
    assert (ca.path / 'private/root.key').read_bytes() == root_before
    assert not (ca.path / '.transaction/commit.json').exists()


def test_interrupted_openssl_working_counter_never_touches_published_ca(tmp_path):
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    before = {name: (ca.path / name).read_bytes() for name in ('index.txt', 'serial', 'crlnumber', 'crl.pem')}
    def interrupted():
        def damage_and_die(self, *args):
            (self.path / 'crlnumber').write_bytes(b'')
            os.kill(os.getpid(), signal.SIGKILL)
        Authority.openssl = damage_and_die
        ca.crl()
    process = multiprocessing.get_context('fork').Process(target=interrupted)
    process.start()
    process.join(20)
    assert process.exitcode == -signal.SIGKILL
    assert all((ca.path / name).read_bytes() == content for name, content in before.items())
    ca.crl()
    ca.check_state()
    archives = list((ca.path / 'interrupted-transactions').iterdir())
    assert len(archives) == 1
    damaged = list(archives[0].glob('work-*/crlnumber'))
    assert len(damaged) == 1 and damaged[0].read_bytes() == b''


def test_corrupt_committed_journal_is_preserved_and_rejected(tmp_path, monkeypatch):
    from vanguard.common import Rejected
    ca = Authority(tmp_path / 'ca')
    ca.initialize()
    original = Publication.publish_file
    def interrupt(*args):
        raise OSError('injected storage failure')
    monkeypatch.setattr(Publication, 'publish_file', interrupt)
    with pytest.raises(Rejected):
        ca.crl()
    monkeypatch.setattr(Publication, 'publish_file', original)
    decision = json.loads((ca.path / '.transaction/commit.json').read_text())
    work = ca.path / '.transaction' / decision['work']
    (work / 'crlnumber').write_bytes(b'')
    before = (ca.path / 'crlnumber').read_bytes()
    with pytest.raises(Rejected, match='operator inspection'):
        ca.crl()
    assert (ca.path / '.transaction/commit.json').exists()
    assert (ca.path / 'crlnumber').read_bytes() == before
