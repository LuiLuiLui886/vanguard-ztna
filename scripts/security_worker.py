#!/usr/bin/env python3
"""Bounded guest helpers for S-03/S-04. No credentials are printed."""

import argparse
import hashlib
import json
import os
import re
import signal
import struct
import subprocess
import time
from pathlib import Path


def command(*args, check=True, timeout=15):
    return subprocess.run(args, capture_output=True, text=True, check=check,
                          timeout=timeout, env={**os.environ, 'LC_ALL': 'C'})


def pcap_summary(data, marker):
    """Reject incomplete captures; inspect packet bytes, never the file header."""
    formats = {b'\xd4\xc3\xb2\xa1': '<', b'\xa1\xb2\xc3\xd4': '>',
               b'\x4d\x3c\xb2\xa1': '<', b'\xa1\xb2\x3c\x4d': '>'}
    if len(data) < 24 or data[:4] not in formats:
        raise ValueError('Invalid classic pcap header')
    endian = formats[data[:4]]
    major, minor, _, _, snaplen, linktype = struct.unpack(endian + 'HHIIII', data[4:24])
    if (major, minor) != (2, 4) or not snaplen:
        raise ValueError('Unsupported pcap version/snaplen')
    offset, count, matches = 24, 0, 0
    while offset < len(data):
        if len(data) - offset < 16:
            raise ValueError('Truncated packet header')
        _, _, size, original = struct.unpack(endian + 'IIII', data[offset:offset + 16])
        offset += 16
        if size != original or size > snaplen or offset + size > len(data):
            raise ValueError('Truncated packet data')
        matches += marker in data[offset:offset + size]
        count += 1
        offset += size
    return {'packets': count, 'marker_packets': matches, 'linktype': linktype,
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def capture(p):
    directory = Path(p['directory'])
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    marker = bytes.fromhex(p['marker'])
    if len(marker) != 16:
        raise ValueError('Marker must contain 16 bytes')
    route = json.loads(command('ip', '-j', 'route', 'get', '192.168.100.20').stdout)[0]
    specs = {'underlay': (route['dev'], 'udp and host 192.168.100.20 and port 51820'),
             'plaintext_control': ('wg0', 'icmp and host 10.8.0.1 and host 10.8.0.2')}
    processes, streams = {}, {}
    try:
        for name, (interface, bpf) in specs.items():
            streams[name] = (directory / (name + '.log')).open('w')
            processes[name] = subprocess.Popen(
                ['tcpdump', '-n', '-U', '-s', '0', '-i', interface,
                 '-w', str(directory / (name + '.pcap')), bpf],
                stdout=subprocess.DEVNULL, stderr=streams[name],
                env={**os.environ, 'LC_ALL': 'C'})
        deadline = time.monotonic() + 5
        for name, proc in processes.items():
            while 'listening on' not in (directory / (name + '.log')).read_text():
                if proc.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError('Capture failed to become ready: ' + name)
                time.sleep(0.05)
        ping = command('ping', '-n', '-c', '10', '-i', '0.1', '-W', '1', '-s', '96',
                       '-p', marker.hex(), '10.8.0.1', timeout=15)
        time.sleep(0.3)
    finally:
        for proc in processes.values():
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
        for proc in processes.values():
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        for stream in streams.values():
            stream.close()
    result = {'ping': ping.stdout, 'captures': {}}
    for name, (interface, bpf) in specs.items():
        log = (directory / (name + '.log')).read_text()
        dropped = re.search(r'(\d+) packets dropped by kernel', log)
        if processes[name].returncode != 0 or not dropped or int(dropped[1]) != 0:
            raise RuntimeError('Capture error/drops: ' + name)
        summary = pcap_summary((directory / (name + '.pcap')).read_bytes(), marker)
        if summary['packets'] < 20:
            raise RuntimeError('Insufficient packets: ' + name)
        result['captures'][name] = {**summary, 'interface': interface, 'filter': bpf,
                                    'kernel_drops': 0}
    if result['captures']['underlay']['marker_packets'] != 0:
        raise RuntimeError('Plaintext marker found on underlay')
    if result['captures']['plaintext_control']['marker_packets'] != 20:
        raise RuntimeError('Missing plaintext positive control')
    return result


def identifiers(p):
    for name in ('namespace', 'interface', 'comment'):
        if not re.fullmatch(r'vgs[a-z0-9]{8}', p[name]):
            raise ValueError('Invalid resource identifier')


def cleanup_client(p):
    identifiers(p)
    namespaces = [line.split()[0] for line in command('ip', 'netns', 'list').stdout.splitlines()]
    if p['namespace'] in namespaces:
        command('ip', 'netns', 'delete', p['namespace'])
    if command('ip', 'link', 'show', p['interface'], check=False).returncode == 0:
        command('ip', 'link', 'delete', p['interface'])
    return {'cleaned': True}


def configure_client(p):
    identifiers(p)
    from vanguard.client import admit
    from vanguard.common import Remote
    if command('ip', 'link', 'show', p['interface'], check=False).returncode == 0:
        raise RuntimeError('Interface already exists')
    if p['namespace'] in [line.split()[0] for line in command('ip', 'netns', 'list').stdout.splitlines()]:
        raise RuntimeError('Namespace already exists')
    admitted = admit(p['directory'], Remote('https://192.168.100.20:8081', '/etc/vanguard/root.crt'))
    if admitted['decision'] != 'ACCEPT' or admitted['tunnel_ip'] != '10.8.0.3':
        raise RuntimeError('Test identity was not admitted at 10.8.0.3')
    try:
        command('ip', 'netns', 'add', p['namespace'])
        command('ip', 'link', 'add', p['interface'], 'type', 'wireguard')
        command('ip', 'link', 'set', p['interface'], 'netns', p['namespace'])
        command('ip', 'netns', 'exec', p['namespace'], 'wg', 'set', p['interface'],
                'private-key', str(Path(p['directory']) / 'wg.key'), 'peer', p['server_key'],
                'allowed-ips', '10.8.0.1/32', 'endpoint', '192.168.100.20:51820')
        command('ip', '-n', p['namespace'], 'address', 'add', '10.8.0.3/32', 'dev', p['interface'])
        command('ip', '-n', p['namespace'], 'link', 'set', p['interface'], 'up')
        command('ip', '-n', p['namespace'], 'route', 'add', '10.8.0.1/32', 'dev', p['interface'])
        return {'admitted': True, 'lease_until': admitted['lease_until']}
    except BaseException:
        cleanup_client(p)
        raise


def firewall_handles(p):
    identifiers(p)
    data = json.loads(command('nft', '-j', 'list', 'chain', 'inet', 'vanguard', 'input').stdout)
    return [obj['rule']['handle'] for obj in data['nftables']
            if obj.get('rule', {}).get('comment') == p['comment']]


def allow_probe(p):
    if firewall_handles(p):
        raise RuntimeError('Test rule already exists')
    command('nft', 'insert', 'rule', 'inet', 'vanguard', 'input', 'iifname', '"wg0"',
            'ip', 'saddr', '10.8.0.3', 'ip', 'daddr', '10.8.0.1',
            'icmp', 'type', 'echo-request', 'counter', 'accept', 'comment', '"' + p['comment'] + '"')
    return {'handles': firewall_handles(p)}


def cleanup_server(p):
    for handle in firewall_handles(p):
        command('nft', 'delete', 'rule', 'inet', 'vanguard', 'input', 'handle', str(handle))
    return {'cleaned': not firewall_handles(p)}


def probe(p):
    identifiers(p)
    count = 25 if p.get('confirm') else 1
    result = command('ip', 'netns', 'exec', p['namespace'], 'ping', '-n', '-c', str(count),
                     '-i', '0.2', '-W', '0.5', '10.8.0.1', check=False, timeout=10)
    match = re.search(r'(\d+) packets transmitted, (\d+) received', result.stdout)
    if result.returncode not in (0, 1) or not match or int(match[1]) != count:
        raise RuntimeError('Probe execution failed: ' + json.dumps({
            'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}))
    return {'sent': int(match[1]), 'received': int(match[2]), 'exit_code': result.returncode}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = {'capture': capture, 'configure': configure_client, 'probe': probe,
               'allow': allow_probe, 'cleanup-client': cleanup_client, 'cleanup-server': cleanup_server}
    parser.add_argument('action', choices=actions)
    parser.add_argument('config', nargs='?', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    import sys
    p = json.loads(args.config.read_text()) if args.config else json.load(sys.stdin)
    print(json.dumps(actions[args.action](p)))


if __name__ == '__main__':
    main()
