#!/usr/bin/env python3
"""Read-only Linux host checks for the approved physical pilot; never applies rules."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

NODES = ('VM-CA', 'VM-SERVER', 'VM-CLIENT', 'VM-ADMIN', 'VM-ATTACKER', 'VM-CLIENT-WINDOWS')
SERVICES = {'VM-CA', 'VM-SERVER', 'VM-ADMIN'}


def probe(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=5, check=False)
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def assess(addresses, forwarding, nodes):
    checks = []
    def add(name, status, reason):
        checks.append({'check': name, 'status': status, 'reason': reason})
    if addresses is None:
        add('host_lan', 'UNKNOWN', 'Cannot inspect IPv4 interfaces')
        add('backend_bridge', 'UNKNOWN', 'Cannot inspect IPv4 interfaces')
    else:
        lan = any(n.get('operstate') == 'UP' and n.get('ifname', '').startswith(('en', 'eth'))
                  and any(a.get('local') == '192.168.50.10' and a.get('prefixlen') == 24
                          for a in n.get('addr_info', [])) for n in addresses)
        bridge = any(n.get('ifname') == 'virbr-vg' and
                     any(a.get('local') == '192.168.100.1' and a.get('prefixlen') == 24
                         for a in n.get('addr_info', [])) for n in addresses)
        add('host_lan', 'PASS' if lan else 'FAIL', 'Expected Ethernet UP at 192.168.50.10/24')
        add('backend_bridge', 'PASS' if bridge else 'FAIL', 'Expected virbr-vg at 192.168.100.1/24; address alone is not connectivity')
    add('forwarding_flag', 'UNKNOWN' if forwarding is None else ('PASS' if forwarding.strip() == '1' else 'FAIL'),
        'IPv4 forwarding flag only; firewall still needs review')
    for name in NODES:
        state = nodes.get(name)
        if state is None:
            add(name, 'UNKNOWN', 'Domain missing or inspection unavailable')
        elif name in SERVICES:
            add(name, 'PASS' if state.strip() == 'running' else 'FAIL', 'Backend domain must be running; this is not service readiness')
        else:
            add(name, 'PASS', 'Domain preserved; not required to run for this pilot')
    add('host_libvirt_firewall', 'MANUAL', 'Review effective forwarding/NAT chains and return path; do not infer from route alone')
    add('backend_https', 'NOT_TESTED', 'Verify CA/server/admin readiness with trusted root from the approved management path')
    add('endpoint_udp_application', 'NOT_TESTED', 'Requires admission, handshake, explicit resource grant and real traffic')
    return {'schema': 1, 'status': 'BLOCKED' if any(c['status'] in ('FAIL', 'UNKNOWN') for c in checks)
            else 'MANUAL_REVIEW_REQUIRED', 'ready_for_production': False, 'mutations': False, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optional new JSON report; refuses overwrite')
    args = parser.parse_args()
    raw = probe(['ip', '-j', '-4', 'address', 'show'])
    try:
        addresses = json.loads(raw) if raw is not None else None
        if not isinstance(addresses, list):
            addresses = None
    except ValueError:
        addresses = None
    report = assess(addresses, probe(['sysctl', '-n', 'net.ipv4.ip_forward']),
                    {name: probe(['virsh', '-c', 'qemu:///system', 'domstate', name]) for name in NODES})
    report['observed_at'] = datetime.now(timezone.utc).isoformat()
    content = json.dumps(report, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(content)
    print(content, end='')
    raise SystemExit(2)  # Always requires manual firewall/target validation, never a deployment approval.


if __name__ == '__main__':
    main()
