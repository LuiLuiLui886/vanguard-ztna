#!/usr/bin/env python3
"""Bounded helpers for the five-node lab benchmark; never print private keys."""

import argparse
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from evidence import save_json
from security_worker import command, configure_client, firewall_handles, identifiers


def validate(p):
    identifiers(p)
    if p['namespace'] != p['interface'] or p['interface'] != p['comment']:
        raise ValueError('Resource names must match')
    if p['mode'] not in ('clear', 'vanguard', 'wireguard'):
        raise ValueError('Unknown condition')
    if not re.fullmatch(r'/var/lib/vanguard/benchmark-[a-f0-9]{12}', p['directory']):
        raise ValueError('Invalid private evidence directory')
    if p['device_id'] != Path(p['directory']).name:
        raise ValueError('Identity must match evidence directory')


def cpu_snapshot():
    return {'monotonic_ns': time.monotonic_ns(),
            'ticks': [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:]]}


def cpu_delta(start, end):
    if len(start['ticks']) < 8 or len(start['ticks']) != len(end['ticks']):
        raise ValueError('Incomplete CPU counters')
    delta = [b - a for a, b in zip(start['ticks'][:8], end['ticks'][:8])]
    duration = (end['monotonic_ns'] - start['monotonic_ns']) / 1e9
    total = sum(delta)  # guest/guest_nice are already included in user/nice.
    if any(x < 0 for x in delta) or total <= 0 or not math.isfinite(duration) or duration <= 0:
        raise ValueError('CPU counters reset/decreased or time window invalid')
    return {'seconds': duration, 'busy_percent': 100 * sum(delta[i] for i in (0, 1, 2, 5, 6)) / total,
            'idle_percent': 100 * delta[3] / total, 'iowait_percent': 100 * delta[4] / total,
            'steal_percent': 100 * delta[7] / total, 'total_ticks': total,
            'boundary': 'server control connection envelope including warmup and finalization'}


def namespace_prefix(p, role):
    return (['ip', 'netns', 'exec', p['namespace']]
            if p['mode'] == 'wireguard' or (role == 'client' and p['mode'] == 'vanguard') else [])


def addresses(p):
    return (('192.168.100.30', '192.168.100.20') if p['mode'] == 'clear'
            else ('10.8.0.3', '10.8.0.1'))


def allow(p):
    validate(p)
    if firewall_handles(p):
        raise RuntimeError('Temporary firewall rules already exist')
    if p['mode'] == 'wireguard':
        if not p.get('wg_exception'):
            raise ValueError('WireGuard baseline requires explicit admission exception')
        specs = [['ip', 'saddr', '192.168.100.30', 'ip', 'daddr', '192.168.100.20',
                  'udp', 'dport', '51821']]
    else:
        source, target = addresses(p)
        interface = ('wg0' if p['mode'] == 'vanguard' else
                     json.loads(command('ip', '-j', 'route', 'get', source).stdout)[0]['dev'])
        scope = ['iifname', '"' + interface + '"', 'ip', 'saddr', source, 'ip', 'daddr', target]
        specs = [scope + ['tcp', 'dport', '5201'], scope + ['udp', 'dport', '5201'],
                 scope + ['icmp', 'type', 'echo-request']]
    for spec in specs:
        command('nft', 'insert', 'rule', 'inet', 'vanguard', 'input', *spec,
                'counter', 'accept', 'comment', '"' + p['comment'] + '"')
    return {'handles': firewall_handles(p)}


def generate_key(p):
    validate(p)
    if p['mode'] != 'wireguard' or not p.get('wg_exception'):
        raise ValueError('Baseline is not authorized')
    from vanguard.common import write_private
    directory = Path(p['directory'])
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    private = command('wg', 'genkey').stdout
    write_private(directory / 'wg.key', private)
    public = subprocess.run(['wg', 'pubkey'], input=private, text=True,
                            capture_output=True, check=True, timeout=5).stdout.strip()
    return {'public_key': public}


def configure(p, role):
    validate(p)
    if p['mode'] == 'vanguard' and role == 'client':
        result = configure_client(p)  # Six checks and employee session before any live peer.
        command('ip', '-n', p['namespace'], 'link', 'set', p['interface'], 'mtu', '1420')
        return result
    if p['mode'] != 'wireguard' or not p.get('wg_exception'):
        raise ValueError('No authorized namespace setup for this condition')
    from vanguard.common import wg_key
    wg_key(p['peer_key'])
    command('ip', 'netns', 'add', p['namespace'])
    command('ip', 'link', 'add', p['interface'], 'type', 'wireguard')
    command('ip', 'link', 'set', p['interface'], 'netns', p['namespace'])
    args = ['ip', 'netns', 'exec', p['namespace'], 'wg', 'set', p['interface'],
            'private-key', str(Path(p['directory']) / 'wg.key')]
    if role == 'server':
        args += ['listen-port', '51821', 'peer', p['peer_key'], 'allowed-ips', '10.8.0.3/32']
    else:
        args += ['peer', p['peer_key'], 'allowed-ips', '10.8.0.1/32',
                 'endpoint', '192.168.100.20:51821']
    command(*args)
    own, other = ('10.8.0.1', '10.8.0.3') if role == 'server' else ('10.8.0.3', '10.8.0.1')
    command('ip', '-n', p['namespace'], 'address', 'add', own + '/32', 'dev', p['interface'])
    command('ip', '-n', p['namespace'], 'link', 'set', p['interface'], 'mtu', '1420', 'up')
    command('ip', '-n', p['namespace'], 'route', 'add', other + '/32', 'dev', p['interface'])
    if role == 'server':
        rules = '''table inet benchmark {
 chain input { type filter hook input priority 0; policy drop;
  ct state established,related accept
  ip saddr 10.8.0.3 ip daddr 10.8.0.1 tcp dport 5201 accept
  ip saddr 10.8.0.3 ip daddr 10.8.0.1 udp dport 5201 accept
  ip saddr 10.8.0.3 ip daddr 10.8.0.1 icmp type echo-request accept
 }
 chain forward { type filter hook forward priority 0; policy drop; }
}
'''
        subprocess.run(namespace_prefix(p, role) + ['nft', '-f', '-'], input=rules,
                       text=True, capture_output=True, check=True, timeout=10)
    return {'configured': True, 'admission': 'explicit isolated baseline exception'}


def cleanup(p, role):
    validate(p)
    errors = []
    # Stop every process holding the namespace before deleting it.
    for suffix in ('tcp', 'udp', 'renew'):
        result = command('systemctl', 'stop', p['comment'] + '-' + suffix + '.service', check=False)
        if result.returncode and 'not loaded' not in result.stderr:
            errors.append(result.stderr)
    if role == 'server':
        for handle in firewall_handles(p):
            command('nft', 'delete', 'rule', 'inet', 'vanguard', 'input', 'handle', str(handle))
    namespaces = [line.split()[0] for line in command('ip', 'netns', 'list').stdout.splitlines()]
    if p['namespace'] in namespaces:
        pids = command('ip', 'netns', 'pids', p['namespace']).stdout.split()
        if pids:
            raise RuntimeError('Namespace still held by processes; retain timer and inspect')
        command('ip', 'netns', 'delete', p['namespace'])
    if command('ip', 'link', 'show', p['interface'], check=False).returncode == 0:
        command('ip', 'link', 'delete', p['interface'])
    if errors:
        raise RuntimeError('Unit cleanup failed: ' + '; '.join(errors))
    return {'cleaned': True}


def cleanup_admin(p):
    validate(p)
    if p['mode'] != 'vanguard':
        return {'cleaned': True}
    from vanguard.admin import create_app
    from vanguard.common import Rejected
    d = create_app().extensions['dashboard']
    try:
        row = d.device(p['device_id'])
        if row['certificate']:
            d.revoke(p['device_id'])
    except Rejected as exc:
        if exc.status != 404:
            raise
    finally:
        try:
            d.server.call('POST', '/api/employees/u-' + p['device_id'] + '/disable', {})
        except Rejected as exc:
            if getattr(exc, 'upstream_status', None) != 404:
                raise
    return {'cleaned': True}


def renew(p):
    validate(p)
    from vanguard.client import admit
    from vanguard.common import Remote
    result = {'status': 'RUNNING', 'leases': []}
    path = Path(p['directory']) / 'renewal.json'
    try:
        for _ in range(12):
            admitted = admit(p['directory'], Remote('https://192.168.100.20:8081',
                                                  '/etc/vanguard/root.crt'))
            if admitted['decision'] != 'ACCEPT' or admitted['tunnel_ip'] != '10.8.0.3':
                raise RuntimeError('Renewal not accepted for test identity')
            result['leases'].append(admitted['lease_until'])
            save_json(path, result)
            time.sleep(10)
    except KeyboardInterrupt:
        result['status'] = 'STOPPED'
    except Exception:
        result['status'] = 'FAIL'
        raise
    finally:
        save_json(path, result)
    return result


def control_connected():
    return any(line.split()[1].split(':')[1] == '1451' and line.split()[3] == '01'
               for line in Path('/proc/net/tcp').read_text().splitlines()[1:])


def serve(p):
    validate(p)
    directory = Path(p['directory'])
    protocol = p['protocol']
    if protocol not in ('tcp', 'udp'):
        raise ValueError('Invalid protocol')
    report = {'status': 'RUNNING', 'protocol': protocol, 'poll_interval_seconds': 0.05}
    output = directory / (protocol + '-server.json')
    save_json(output, report)
    proc = None
    try:
        with (directory / (protocol + '-server-raw.json')).open('w') as stream:
            proc = subprocess.Popen(['iperf3', '-4', '-s', '-1', '-J', '-B', addresses(p)[1],
                                     '-p', '5201'], stdout=stream, stderr=subprocess.STDOUT)
            started, previous, gaps = time.monotonic(), cpu_snapshot(), []
            while proc.poll() is None:
                current = cpu_snapshot()
                gaps.append((current['monotonic_ns'] - previous['monotonic_ns']) / 1e9)
                if 'cpu_start' not in report and control_connected():
                    report['cpu_start'] = previous
                    save_json(output, report)
                previous = current
                if time.monotonic() - started > 40:
                    raise RuntimeError('Server timed out')
                time.sleep(0.05)
            report['cpu_end'] = cpu_snapshot()
        if proc.returncode or 'cpu_start' not in report:
            raise RuntimeError('iperf server failed or control connection not observed')
        report['cpu'] = cpu_delta(report['cpu_start'], report['cpu_end'])
        report['max_poll_gap_seconds'] = max(gaps)
        report['iperf'] = json.loads((directory / (protocol + '-server-raw.json')).read_text())
        if report['iperf'].get('error'):
            raise RuntimeError('iperf server reported error')
        report['status'] = 'COMPLETE'
    except BaseException as exc:
        report.update(status='FAIL', error=str(exc))
        raise
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        save_json(output, report)
    return {'status': report['status']}


def transfer(p):
    validate(p)
    protocol = p['protocol']
    if protocol not in ('tcp', 'udp'):
        raise ValueError('Invalid protocol')
    args = namespace_prefix(p, 'client') + ['iperf3', '-4', '-c', addresses(p)[1],
            '-B', addresses(p)[0], '-p', '5201', '-J', '-t', '10', '-O', '2', '-P', '1']
    if protocol == 'udp':
        args += ['-u', '-b', '10M', '-l', '1200']
    result = command(*args, check=False, timeout=30)
    output = Path(p['directory']) / (protocol + '-client.json')
    save_json(output, {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        raise RuntimeError('iperf client failed; inspect private result file')
    return json.loads(result.stdout)


def ping(p):
    validate(p)
    result = command(*namespace_prefix(p, 'client'), 'ping', '-n', '-c', '30', '-i', '0.1',
                     '-W', '1', '-s', '56', addresses(p)[1], check=False, timeout=35)
    save_json(Path(p['directory']) / 'ping.json',
              {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = {'allow': allow, 'key': generate_key, 'configure-client': lambda p: configure(p, 'client'),
               'configure-server': lambda p: configure(p, 'server'),
               'cleanup-client': lambda p: cleanup(p, 'client'),
               'cleanup-server': lambda p: cleanup(p, 'server'), 'cleanup-admin': cleanup_admin,
               'renew': renew, 'serve': serve, 'transfer': transfer, 'ping': ping}
    parser.add_argument('action', choices=actions)
    parser.add_argument('config', nargs='?', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    def stop(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    p = json.loads(args.config.read_text()) if args.config else json.load(sys.stdin)
    print(json.dumps(actions[args.action](p)))


if __name__ == '__main__':
    main()
