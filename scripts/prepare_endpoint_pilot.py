#!/usr/bin/env python3
"""Generate public pilot artifacts only. Never execute network/VM mutations."""

import argparse
import json
from pathlib import Path

from vanguard.pki import fingerprint, load_cert
from vanguard.profile import validate_profile


def prepare(root_certificate, server_key, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Output exists; do not overwrite operator configuration')
    profile = validate_profile({
        'schema': 1, 'api_url': 'https://192.168.100.20:8081',
        'wireguard_host': '192.168.100.20', 'wireguard_port': 51820,
        'server_public_key': server_key, 'root_sha256': fingerprint(load_cert(Path(root_certificate).read_bytes())),
        'backend_network': '192.168.100.0/24', 'tunnel_network': '10.8.0.0/24',
        'allowed_ips': ['10.8.0.1/32'],
        'resources': [{'name': 'internal-demo', 'address': '10.8.0.1', 'protocol': 'tcp', 'port': 8082}],
    })
    output.mkdir(parents=True)
    (output / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
    (output / 'root.crt').write_bytes(Path(root_certificate).read_bytes())
    (output / 'admin-public.env').write_text(
        '# Candidate VM-ADMIN values only; preserve all other installed environment values.\n'
        'VANGUARD_CLIENT_PROFILE=/etc/vanguard/endpoint-profile.json\n'
        '# VM-SERVER listen=192.168.100.20:8081 ; wg=192.168.100.20:51820\n')
    plan = {'schema': 1, 'status': 'REQUIRES_OPERATOR_NETWORK_REVIEW',
            'router': '192.168.50.1', 'host': '192.168.50.10',
            'pc_lan': '192.168.50.20', 'laptop_wifi': '192.168.50.30',
            'endpoint_route': {'destination': '192.168.100.20/32', 'next_hop': '192.168.50.10'},
            'allowed_transports': [{'protocol': 'tcp', 'port': 8081}, {'protocol': 'udp', 'port': 51820}],
            'server': '192.168.100.20', 'return_route_via': '192.168.100.1',
            'host_forwarding': 'must be verified before application',
            'host_firewall_backend': 'UNCONFIRMED; libvirt chain/backend review required',
            'reserved_tunnel_ips': ['10.8.0.2', '10.8.0.3', '10.8.0.4'],
            'proposed_tunnel_ips': {'pc': '10.8.0.5', 'laptop': '10.8.0.6'},
            'allocation_confirmed': False, 'automatic_peer': False}
    (output / 'network-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--server-public-key-file', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.root, args.server_public_key_file.read_text().strip(), args.output)
    print('Public candidate prepared; no routes, firewall, certificates or peers applied.')


if __name__ == '__main__':
    main()
