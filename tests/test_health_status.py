import json
import subprocess
from types import SimpleNamespace

from conftest import register

from vanguard import health
from vanguard.client import admit
from vanguard.common import Rejected, database
from vanguard.server import WireGuard, notify_supervisor


def test_ca_readiness_is_read_only_and_detects_corruption(lab, monkeypatch):
    path = lab['ca'].path
    monkeypatch.setenv('VANGUARD_CA_DIR', str(path))
    before = {name: (path / name).read_bytes() for name in ('serial', 'crlnumber', 'crl.pem', 'index.txt')}
    assert health.probe('ca')['status'] == 'ready'
    assert all((path / name).read_bytes() == data for name, data in before.items())
    (path / 'serial').write_text('')
    assert health.probe('ca')['status'] == 'not_ready'
    assert (path / 'serial').read_bytes() == b''


def test_readiness_deadline_becomes_unknown(monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs['timeout'] == 6
        raise subprocess.TimeoutExpired('probe', 6)
    monkeypatch.setattr(health.subprocess, 'run', timeout)
    assert health.bounded_readiness('ca') == {'status': 'not_ready', 'checks': {'probe': 'unknown'}}


def test_status_separates_lease_and_peer_and_unknown(lab, monkeypatch):
    register(lab)
    row = lab['admission'].listing()[0]
    assert row['registered'] and not row['lease_valid'] and row['peer_present'] is False
    admit(lab['directory'], lab['remote'])
    lab['wg'].active.clear()
    row = lab['admission'].listing()[0]
    assert row['lease_valid'] and row['peer_present'] is False
    def unavailable():
        raise Rejected('inspection failed')
    monkeypatch.setattr(lab['wg'], 'peers', unavailable)
    row = lab['admission'].listing()[0]
    assert row['peer_present'] is None and row['live'] is None
    assert row['last_handshake'] is None and row['rx_bytes'] is None


def test_wireguard_observation_never_reads_private_dump(monkeypatch):
    from vanguard import server
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        assert kwargs['timeout'] == 1
        return SimpleNamespace(stdout={'peers': b'public\n', 'latest-handshakes': b'public\t100\n',
                                       'transfer': b'public\t12\t34\n'}[args[-1]])
    monkeypatch.setattr(server, 'run', command)
    assert WireGuard().observations()['public'] == {'last_handshake': 100, 'rx_bytes': 12, 'tx_bytes': 34}
    assert not any('dump' in args for args in calls)


def test_watchdog_notification_uses_local_socket(tmp_path, monkeypatch):
    import socket
    target = str(tmp_path / 'notify.sock')
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
        receiver.bind(target)
        receiver.settimeout(1)
        monkeypatch.setenv('NOTIFY_SOCKET', target)
        notify_supervisor('WATCHDOG=1')
        assert receiver.recv(256) == b'WATCHDOG=1'


def test_heartbeat_from_another_boot_is_not_ready(tmp_path):
    (tmp_path / 'daemon-heartbeat.json').write_text(json.dumps({
        'boot_id': 'old-boot', 'monotonic': 0, 'crl_available': True}))
    assert health.daemon_fresh(tmp_path) is False


def test_lease_status_checks_session_before_daemon_reconciles(lab):
    register(lab)
    admit(lab['directory'], lab['remote'])
    with database(lab['admission'].db) as db:
        db.execute('UPDATE employee_sessions SET expires=0')
    row = lab['admission'].listing()[0]
    assert row['peer_present'] is True
    assert row['lease_valid'] is False
