#!/usr/bin/env python3
"""Reproducible, bounded performance pilots/series on the existing five-node lab."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import random
import re
import shlex
import signal
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from benchmark_worker import addresses, cpu_delta, namespace_prefix
from evidence import save_json
from verify_lab import Verification


def finite(value, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Metric is not numeric')
    if not math.isfinite(value) or value < minimum:
        raise ValueError('Metric is nonfinite or out of range')
    return value


def parse_transfer(client, server, protocol):
    if server.get('status') != 'COMPLETE' or client.get('error'):
        raise ValueError('Incomplete/failed transfer')
    raw = server['iperf']
    if raw.get('error'):
        raise ValueError('Server transfer error')
    for result in (client, raw):
        spec = result['start']['test_start']
        if (spec['protocol'] != protocol.upper() or spec['num_streams'] != 1
                or spec['duration'] != 10 or spec['omit'] != 2 or spec['reverse'] != 0):
            raise ValueError('Unexpected transfer parameters')
        if protocol == 'udp' and spec['blksize'] != 1200:
            raise ValueError('Unexpected UDP payload')
    received = raw['end']['sum_received' if protocol == 'tcp' else 'sum']
    if received.get('sender') is not False:
        raise ValueError('Receiver result required')
    seconds = finite(received['seconds'])
    if not 9.5 <= seconds <= 11:
        raise ValueError('Incomplete measurement duration')
    size = finite(received['bytes'], 1 if protocol == 'tcp' else 0)
    rate = finite(received['bits_per_second'], 1 if protocol == 'tcp' else 0)
    if not math.isclose(size * 8 / seconds, rate, rel_tol=0.01):
        raise ValueError('Inconsistent receiver rate/bytes/duration')
    cpu = cpu_delta(server['cpu_start'], server['cpu_end'])
    if not 11.5 <= cpu['seconds'] <= 16 or finite(server['max_poll_gap_seconds']) > 0.5:
        raise ValueError('CPU observation envelope is incomplete or polling stalled')
    result = {'receiver_mbps': rate / 1e6, 'receiver_bytes': size, 'seconds': seconds,
              'server_cpu': cpu, 'cpu_max_poll_gap_seconds': server['max_poll_gap_seconds']}
    if protocol == 'udp':
        lost, packets = finite(received['lost_packets']), finite(received['packets'], 1)
        loss = finite(received['lost_percent'])
        if lost > packets or loss > 100 or not math.isclose(loss, 100 * lost / packets, abs_tol=0.01):
            raise ValueError('Inconsistent UDP packet loss')
        result.update(jitter_ms=finite(received['jitter_ms']), lost_packets=lost,
                      packets=packets, loss_percent=loss, offered_mbps=10)
        if size == 0 and rate == 0 and packets > lost:
            # Ubuntu iperf 3.9 with omit can report valid UDP loss/jitter but zero bytes.
            # UDP goodput is optional; never reconstruct it from inconsistent counters.
            result.update(receiver_mbps=None, receiver_bytes=None,
                          goodput_unavailable='iperf receiver byte/rate counters missing')
    else:
        result['sender_retransmits'] = finite(client['end']['sum_sent']['retransmits'])
    return result


def parse_ping(result):
    text = result['stdout']
    count = re.search(r'(\d+) packets transmitted, (\d+) received', text)
    timing = re.search(r'rtt min/avg/max/mdev = ([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+) ms', text)
    if result['returncode'] != 0 or not count or not timing or int(count[1]) != 30 or int(count[2]) != 30:
        raise ValueError('RTT pilot needs 30 successful replies')
    values = [finite(float(x)) for x in timing.groups()]
    if not values[0] <= values[1] <= values[2]:
        raise ValueError('Invalid RTT summary')
    return dict(zip(('min_ms', 'mean_ms', 'max_ms', 'mdev_ms'), values), sent=30, received=30,
                loss_percent=0)


def stats(values):
    for value in values:
        finite(value)
    return {'n': len(values), 'mean': statistics.mean(values), 'median': statistics.median(values),
            'min': min(values), 'max': max(values),
            'sample_sd': statistics.stdev(values) if len(values) > 1 else None}


def summarize(rows, modes, blocks):
    expected = {(b, m) for b in range(1, blocks + 1) for m in modes}
    actual = [(r['block'], r['mode']) for r in rows]
    if (set(actual) != expected or len(actual) != len(expected)
            or any(r.get('status') != 'PASS' or r.get('cleanup', {}).get('status') != 'PASS'
                   for r in rows)):
        raise ValueError('Missing, duplicate, failed or uncleaned conditions')
    return {mode: {'tcp_receiver_mbps': stats([r['tcp']['receiver_mbps'] for r in rows if r['mode'] == mode]),
                   'rtt_mean_ms': stats([r['rtt']['mean_ms'] for r in rows if r['mode'] == mode]),
                   'udp_jitter_ms': stats([r['udp']['jitter_ms'] for r in rows if r['mode'] == mode]),
                   'udp_loss_percent': stats([r['udp']['loss_percent'] for r in rows if r['mode'] == mode]),
                   'tcp_server_busy_percent': stats([r['tcp']['server_cpu']['busy_percent']
                                                     for r in rows if r['mode'] == mode]),
                   'udp_server_busy_percent': stats([r['udp']['server_cpu']['busy_percent']
                                                     for r in rows if r['mode'] == mode])}
            for mode in modes}


def authorize(phase, modes, exception):
    if not modes or len(modes) != len(set(modes)) or set(modes) - {'clear', 'vanguard', 'wireguard'}:
        raise ValueError('Invalid/duplicate condition selection')
    if 'wireguard' in modes and not exception:
        raise ValueError('WG without admission requires an explicit user-approved exception reference')
    if phase == 'series' and set(modes) != {'clear', 'vanguard', 'wireguard'}:
        raise ValueError('Formal series requires all three conditions; use pilot for partial work')


class Benchmark(Verification):
    def __init__(self, inventory, state, phase, modes, seed, exception=None):
        authorize(phase, modes, exception)
        super().__init__(inventory, state)
        self.output = state / 'benchmark-results.json'
        if self.output.exists():
            raise ValueError('Evidence exists; choose a new state directory')
        self.tools = '/var/lib/vanguard/benchmark-tools-' + uuid.uuid4().hex[:12]
        self.blocks = 10 if phase == 'series' else 1
        self.modes, self.exception = modes, exception
        rng = random.Random(seed)
        self.order = [rng.sample(modes, len(modes)) for _ in range(self.blocks)]
        self.report = {'status': 'RUNNING', 'phase': phase, 'utc': datetime.now(timezone.utc).isoformat(),
                       'seed': seed, 'order': self.order, 'remote_tools': self.tools,
                       'wg_exception_reference': exception, 'rounds': [],
                       'cpu_boundary': 'control connection envelope including warmup/finalization'}
        self.save()

    def ssh(self, role, command, data=None, timeout=45):
        return super().ssh(role, command, data, timeout)

    def save(self):
        save_json(self.output, self.report)

    def worker(self, role, action, p, timeout=40):
        return json.loads(self.ssh(role, 'sudo /opt/vanguard/venv/bin/python '
                                  + shlex.quote(self.tools + '/benchmark_worker.py') + ' ' + action,
                                  json.dumps(p).encode(), timeout=timeout))

    def stage(self, row, name):
        if time.monotonic() > self.deadline:
            raise RuntimeError('Condition exceeded 120-second budget')
        row['current_step'] = name
        self.save()

    def watchdog(self, role, p):
        path = self.tools + '/' + p['comment'] + '.json'
        self.write(role, path, json.dumps(p).encode(), owner='vanguard' if role == 'admin' else None)
        unit = p['comment'] + '-cleanup-' + role
        options = (' --property=User=vanguard --property=EnvironmentFile=/etc/vanguard/admin.env'
                   if role == 'admin' else '')
        self.ssh(role, 'sudo systemd-run --unit=' + unit + ' --on-active=180s'
                 ' --timer-property=AccuracySec=1s --property=RuntimeMaxSec=45s' + options
                 + ' /opt/vanguard/venv/bin/python ' + self.tools + '/benchmark_worker.py'
                 + ' cleanup-' + role + ' ' + path)
        return unit

    def transient(self, role, p, action, suffix, prefix=()):
        path = self.tools + '/' + p['comment'] + '-' + suffix + '.json'
        self.write(role, path, json.dumps(p).encode())
        args = ['sudo', 'systemd-run', '--collect', '--unit=' + p['comment'] + '-' + suffix,
                '--property=RuntimeMaxSec=' + ('120s' if action == 'renew' else '45s'),
                '--property=TimeoutStopSec=5s', '--property=KillMode=control-group',
                *prefix, '/opt/vanguard/venv/bin/python', self.tools + '/benchmark_worker.py', action, path]
        self.ssh(role, shlex.join(args))

    def inspect(self, role):
        return json.loads(self.python(role, '''import json,subprocess,pathlib,os
def run(*args): return subprocess.check_output(args,text=True).strip()
print(json.dumps({'kernel':run('uname','-r'),'iperf':run('iperf3','--version'),
 'vcpus':os.cpu_count(),'meminfo':pathlib.Path('/proc/meminfo').read_text(),
 'loadavg':pathlib.Path('/proc/loadavg').read_text(),'cpu_stat':pathlib.Path('/proc/stat').read_text().splitlines()[0],
 'links':json.loads(run('ip','-j','link')), 'routes':json.loads(run('ip','-j','route')),
 'namespaces':run('ip','netns','list'), 'rules':run('nft','-s','list','ruleset')}))
'''))

    def condition(self, row):
        self.deadline = time.monotonic() + 120
        tag, name = 'vgs' + uuid.uuid4().hex[:8], 'benchmark-' + uuid.uuid4().hex[:12]
        p = {'namespace': tag, 'interface': tag, 'comment': tag, 'mode': row['mode'],
             'device_id': name, 'directory': '/var/lib/vanguard/' + name,
             'wg_exception': bool(self.exception)}
        row.update(resources=p, watchdogs={}, cleanup={'status': 'PENDING'})
        self.save()
        snapshots, units, attempted_identity = {}, {}, False
        try:
            for role in ('client', 'server'):
                snapshots[role] = self.inspect(role)
                save_json(self.state / (name + '-' + role + '-before.json'), snapshots[role])
                if snapshots[role]['namespaces']:
                    raise RuntimeError('Existing network namespace; resolve earlier experiment first')
            self.stage(row, 'watchdogs')
            for role in (('client', 'server', 'admin') if p['mode'] == 'vanguard' else ('client', 'server')):
                # Record planned timer before attempting remote creation for interrupted SSH recovery.
                units[role] = tag + '-cleanup-' + role
                row['watchdogs'] = units.copy()
                self.save()
                self.watchdog(role, p)
            self.stage(row, 'identity')
            if p['mode'] == 'vanguard':
                attempted_identity = True
                self.ssh('client', 'sudo /opt/vanguard/venv/bin/vanguard-client --directory '
                         + p['directory'] + ' init --device-id ' + name)
                request = json.loads(self.ssh('client', 'sudo cat ' + p['directory'] + '/request.json'))
                request['tunnel_ip'] = '10.8.0.3'
                certificate = self.register_identity(request, p['directory'])
                self.write('client', p['directory'] + '/device.crt', certificate)
                if request['wg_public_key'] in self.ssh('server', 'sudo wg show wg0 peers').decode().split():
                    raise RuntimeError('Registration unexpectedly added live peer')
                row['registry_only'] = True
                p['server_key'] = self.ssh('server', 'sudo cat /etc/vanguard/server-wg.pub').decode().strip()
                self.ssh('server', 'sudo install -d -m 0700 ' + p['directory'])
            elif p['mode'] == 'wireguard':
                keys = {role: self.worker(role, 'key', p)['public_key'] for role in ('client', 'server')}
                row['baseline_public_keys'] = keys
            else:
                for role in ('client', 'server'):
                    self.ssh(role, 'sudo install -d -m 0700 ' + p['directory'])
            self.stage(row, 'temporary_access')
            row['firewall'] = self.worker('server', 'allow', p)
            if p['mode'] == 'vanguard':
                row['admission'] = self.worker('client', 'configure-client', p)
                self.transient('client', p, 'renew', 'renew')
            elif p['mode'] == 'wireguard':
                for role, other in (('server', 'client'), ('client', 'server')):
                    self.worker(role, 'configure-' + role, {**p, 'peer_key': keys[other]})
            self.stage(row, 'warmup_and_rtt')
            prefix = namespace_prefix(p, 'client')
            # Establish handshake before the 30-packet RTT sample.
            self.ssh('client', shlex.join(['sudo', *prefix, 'ping', '-c', '3', '-W', '2', addresses(p)[1]]))
            time.sleep(5)
            row['rtt_raw'] = self.worker('client', 'ping', p)
            row['rtt'] = parse_ping(row['rtt_raw'])
            for protocol in ('tcp', 'udp'):
                self.stage(row, protocol)
                config = {**p, 'protocol': protocol}
                self.transient('server', config, 'serve', protocol, namespace_prefix(p, 'server'))
                ready_deadline = time.monotonic() + 8
                while True:
                    listening = self.ssh('server', shlex.join(['sudo', *namespace_prefix(p, 'server'),
                                                   'ss', '-H', '-ltn', 'sport', '=', ':5201']))
                    if listening.strip():
                        break
                    if time.monotonic() > ready_deadline:
                        raise RuntimeError('iperf server did not listen')
                    time.sleep(0.2)
                client = self.worker('client', 'transfer', config)
                save_json(self.state / (name + '-' + protocol + '-client.json'), client)
                for _ in range(15):
                    server = json.loads(self.ssh('server', 'sudo cat ' + p['directory']
                                                 + '/' + protocol + '-server.json'))
                    if server['status'] != 'RUNNING':
                        break
                    time.sleep(0.2)
                save_json(self.state / (name + '-' + protocol + '-server.json'), server)
                row[protocol] = parse_transfer(client, server, protocol)
                self.save()
            if p['mode'] == 'vanguard':
                renewal = json.loads(self.ssh('client', 'sudo cat ' + p['directory'] + '/renewal.json'))
                if renewal['status'] == 'FAIL' or len(set(renewal['leases'])) < 2:
                    raise RuntimeError('Admission renewal not demonstrated')
                row['renewal'] = renewal
            self.stage(row, 'measurements_complete')
        finally:
            if sys.exc_info()[0]:
                row['failed_step'] = row.get('current_step')
            row['current_step'] = 'cleanup'
            self.save()
            errors = []
            for role in ('client', 'server'):
                if role in units:
                    try:
                        self.worker(role, 'cleanup-' + role, p)
                        self.ssh(role, 'sudo systemctl stop ' + units[role] + '.timer')
                    except Exception as exc:
                        errors.append(role + ': ' + str(exc))
            if attempted_identity:
                try:
                    self.cleanup_identity(name)
                    self.ssh('admin', 'sudo systemctl stop ' + units['admin'] + '.timer')
                except Exception as exc:
                    errors.append('identity: ' + str(exc))
            elif 'admin' in units:
                try:
                    self.ssh('admin', 'sudo systemctl stop ' + units['admin'] + '.timer')
                except Exception as exc:
                    errors.append('unused admin watchdog: ' + str(exc))
            for role, before in snapshots.items():
                try:
                    after = self.inspect(role)
                    save_json(self.state / (name + '-' + role + '-after.json'), after)
                    if (before['rules'] != after['rules'] or before['routes'] != after['routes']
                            or before['namespaces'] != after['namespaces']
                            or {x['ifname'] for x in before['links']} != {x['ifname'] for x in after['links']}):
                        raise RuntimeError('Firewall/routes/interfaces/namespaces not restored')
                except Exception as exc:
                    errors.append('restore ' + role + ': ' + str(exc))
            try:
                self.ssh('client', 'ping -c 2 -W 2 10.8.0.1 >/dev/null')
            except Exception as exc:
                errors.append('main ping: ' + str(exc))
            row['cleanup'] = {'status': 'FAIL' if errors else 'PASS', 'errors': errors}
            self.save()
            if errors:
                raise RuntimeError('Cleanup incomplete; inspect recorded resources')

    def run(self):
        try:
            # Refuse a second test identity; no main identity is modified.
            self.python('server', """import sqlite3
c=sqlite3.connect('file:/var/lib/vanguard/server/server.db?mode=ro',uri=True)
assert not c.execute("SELECT 1 FROM devices WHERE enabled=1 AND tunnel_ip='10.8.0.3'").fetchone(), '10.8.0.3 already reserved'
""")
            for role in ('client', 'server', 'admin'):
                self.ssh(role, 'sudo install -d -m 0700 ' + ('-o vanguard ' if role == 'admin' else '') + self.tools)
                for name in ('benchmark_worker.py', 'security_worker.py', 'evidence.py'):
                    self.write(role, self.tools + '/' + name, (Path(__file__).parent / name).read_bytes(),
                               owner='vanguard' if role == 'admin' else None)
            self.report['worker_sha256'] = hashlib.sha256(
                (Path(__file__).parent / 'benchmark_worker.py').read_bytes()).hexdigest()
            for block, order in enumerate(self.order, 1):
                for mode in order:
                    row = {'block': block, 'mode': mode, 'status': 'RUNNING'}
                    self.report['rounds'].append(row)
                    self.save()
                    self.condition(row)
                    row.update(status='PASS', current_step=None)
                    self.save()
                    print(f'PASS benchmark {mode} block {block}/{self.blocks}', flush=True)
            self.report['summary'] = summarize(self.report['rounds'], self.modes, self.blocks)
            self.report['status'] = 'COMPLETE'
        except BaseException as exc:
            self.report.update(status='INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAIL',
                               error=str(exc))
            if self.report['rounds'] and self.report['rounds'][-1]['status'] == 'RUNNING':
                self.report['rounds'][-1]['status'] = self.report['status']
            raise
        finally:
            self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('phase', choices=('pilot', 'series'))
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--modes', nargs='+', choices=('clear', 'vanguard', 'wireguard'),
                        default=['clear', 'vanguard'])
    parser.add_argument('--seed', type=int, default=20261010)
    parser.add_argument('--wg-exception-reference', help='Record the explicit user approval; not implied by this flag')
    args = parser.parse_args()
    try:
        authorize(args.phase, args.modes, args.wg_exception_reference)
    except ValueError as exc:
        parser.error(str(exc))
    os.umask(0o077)
    def interrupt(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    Path('state').mkdir(exist_ok=True)
    with Path('state/benchmark.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        Benchmark(json.loads(args.inventory.read_text()), args.state, args.phase, args.modes,
                  args.seed, args.wg_exception_reference).run()


if __name__ == '__main__':
    main()
