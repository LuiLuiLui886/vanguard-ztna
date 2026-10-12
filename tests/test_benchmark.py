import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import benchmark_worker as worker
from verify_benchmark import authorize, parse_ping, parse_transfer, summarize


def params(mode='clear'):
    return {'namespace': 'vgs1234abcd', 'interface': 'vgs1234abcd', 'comment': 'vgs1234abcd',
            'mode': mode, 'device_id': 'benchmark-123456abcdef',
            'directory': '/var/lib/vanguard/benchmark-123456abcdef'}


def evidence(protocol='tcp'):
    spec = {'protocol': protocol.upper(), 'num_streams': 1, 'duration': 10,
            'omit': 2, 'reverse': 0, 'blksize': 1200}
    received = {'sender': False, 'seconds': 10, 'bytes': 12_500_000,
                'bits_per_second': 10_000_000, 'lost_packets': 1, 'packets': 100,
                'lost_percent': 1, 'jitter_ms': 0.05}
    start = {'monotonic_ns': 1_000_000_000, 'ticks': [100] * 10}
    end = {'monotonic_ns': 13_000_000_000,
           'ticks': [140, 110, 120, 120, 102, 102, 104, 102, 120, 110]}
    raw = {'start': {'test_start': spec}, 'end': {'sum_received': received, 'sum': received}}
    client = copy.deepcopy(raw)
    client['end']['sum_sent'] = {'retransmits': 2}
    server = {'status': 'COMPLETE', 'iperf': raw, 'cpu_start': start, 'cpu_end': end,
              'max_poll_gap_seconds': 0.06}
    return client, server


def test_cpu_guest_not_double_counted_and_steal_iowait_separate():
    _, server = evidence()
    cpu = worker.cpu_delta(server['cpu_start'], server['cpu_end'])
    assert cpu['total_ticks'] == 100
    assert cpu['busy_percent'] == 76
    assert cpu['idle_percent'] == 20
    assert cpu['iowait_percent'] == cpu['steal_percent'] == 2
    assert cpu['seconds'] == 12


@pytest.mark.parametrize('change', ['backwards_time', 'counter_reset', 'iowait_decrease', 'missing'])
def test_invalid_cpu_window_rejected(change):
    _, server = evidence()
    if change == 'backwards_time':
        server['cpu_end']['monotonic_ns'] = 0
    elif change == 'missing':
        server['cpu_end']['ticks'] = [1]
    else:
        server['cpu_end']['ticks'][4 if change == 'iowait_decrease' else 0] = 0
    with pytest.raises(ValueError):
        worker.cpu_delta(server['cpu_start'], server['cpu_end'])


@pytest.mark.parametrize('protocol', ['tcp', 'udp'])
def test_receiver_metrics_and_cpu_have_distinct_windows(protocol):
    client, server = evidence(protocol)
    result = parse_transfer(client, server, protocol)
    assert result['receiver_mbps'] == 10
    assert result['seconds'] == 10
    assert result['server_cpu']['seconds'] == 12
    if protocol == 'udp':
        assert result['jitter_ms'] == 0.05 and result['loss_percent'] == 1


@pytest.mark.parametrize('change', ['incomplete', 'sender', 'duration', 'nan', 'rate', 'protocol',
                                   'polling_stall', 'loss', 'payload'])
def test_malformed_transfer_cannot_be_reported(change):
    client, server = evidence('udp')
    received = server['iperf']['end']['sum']
    if change == 'incomplete':
        server['status'] = 'RUNNING'
    elif change == 'sender':
        received['sender'] = True
    elif change == 'duration':
        received['seconds'] = 2
    elif change == 'nan':
        received['jitter_ms'] = float('nan')
    elif change == 'rate':
        received['bits_per_second'] = 100
    elif change == 'protocol':
        client['start']['test_start']['protocol'] = 'TCP'
    elif change == 'polling_stall':
        server['max_poll_gap_seconds'] = 2
    elif change == 'loss':
        received['lost_packets'] = 200
    else:
        client['start']['test_start']['blksize'] = 8000
    with pytest.raises(ValueError):
        parse_transfer(client, server, 'udp')


def test_rtt_requires_full_reply_evidence():
    result = {'returncode': 0, 'stdout': '30 packets transmitted, 30 received\n'
              'rtt min/avg/max/mdev = 0.1/0.2/0.3/0.04 ms'}
    assert parse_ping(result)['mean_ms'] == 0.2
    with pytest.raises(ValueError):
        parse_ping({**result, 'stdout': result['stdout'].replace('30 received', '29 received')})


def test_iperf39_udp_missing_goodput_does_not_invent_throughput():
    client, server = evidence('udp')
    server['iperf']['end']['sum'].update(bytes=0, bits_per_second=0)
    result = parse_transfer(client, server, 'udp')
    assert result['receiver_mbps'] is None and result['receiver_bytes'] is None
    assert result['loss_percent'] == 1 and result['jitter_ms'] == 0.05
    client, server = evidence('tcp')
    server['iperf']['end']['sum_received'].update(bytes=0, bits_per_second=0)
    with pytest.raises(ValueError):
        parse_transfer(client, server, 'tcp')


def test_default_permission_excludes_unadmitted_baseline(monkeypatch):
    authorize('pilot', ['clear', 'vanguard'], None)
    with pytest.raises(ValueError):
        authorize('pilot', ['wireguard'], None)
    with pytest.raises(ValueError):
        authorize('series', ['clear', 'vanguard'], None)
    calls = []
    monkeypatch.setattr(worker, 'command', lambda *args, **kw: calls.append(args))
    with pytest.raises(ValueError):
        worker.configure(params('wireguard'), 'server')
    assert calls == []


@pytest.mark.parametrize('field,value', [('interface', 'wg0'), ('namespace', 'VM-CLIENT'),
                                       ('directory', '/var/lib/vanguard/client'),
                                       ('directory', '/var/lib/vanguard/benchmark-123456abcdef/..'),
                                       ('comment', 'vgs1234abcd;id')])
def test_cleanup_cannot_target_main_identity_or_shell_syntax(field, value, monkeypatch):
    p = {**params(), field: value}
    calls = []
    monkeypatch.setattr(worker, 'command', lambda *args, **kw: calls.append(args))
    with pytest.raises(ValueError):
        worker.cleanup(p, 'client')
    assert calls == []


def test_firewall_allow_scope_is_only_test_source_and_port(monkeypatch):
    calls = []
    monkeypatch.setattr(worker, 'firewall_handles', lambda p: [])
    monkeypatch.setattr(worker, 'command', lambda *args, **kw: calls.append(args))
    worker.allow(params('vanguard'))
    assert len(calls) == 3
    for call in calls:
        assert ('"wg0"', 'ip', 'saddr', '10.8.0.3', 'ip', 'daddr', '10.8.0.1') == call[7:14]
        assert 'flush' not in call and '10.8.0.2' not in call


def test_summary_refuses_duplicate_partial_or_failed_cleanup():
    client, server = evidence()
    transfer = parse_transfer(client, server, 'tcp')
    row = {'status': 'PASS', 'cleanup': {'status': 'PASS'}, 'block': 1, 'mode': 'clear',
           'tcp': transfer, 'udp': {**transfer, 'jitter_ms': 0.1, 'loss_percent': 0},
           'rtt': {'mean_ms': 0.1}}
    assert summarize([row], ['clear'], 1)['clear']['tcp_receiver_mbps']['sample_sd'] is None
    for rows, blocks in (([row, row], 1), ([row], 10), ([{**row, 'cleanup': {'status': 'FAIL'}}], 1)):
        with pytest.raises(ValueError):
            summarize(rows, ['clear'], blocks)
