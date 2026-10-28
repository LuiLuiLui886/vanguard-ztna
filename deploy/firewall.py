#!/usr/bin/env python3
"""Install the documented firewall on ONE existing VanGuard Ubuntu 22.04 VM.

Uses only the dedicated inet/vanguard nftables table. A scheduled rollback removes
that table after 120 seconds unless the operator confirms access through a fresh
SSH connection with `systemctl stop vanguard-firewall-rollback.timer`.
"""

import argparse
import ipaddress
import json
import os
import re
import subprocess
from pathlib import Path

ADDRESSES = {"ca": 10, "server": 20, "client": 30, "admin": 40, "attacker": 50}


def rules(role, management, windows_client=False, application_policy=False, physical_clients=(), internet_uplink=None):
    management = str(ipaddress.IPv4Address(management))
    physical = [str(ipaddress.IPv4Address(value)) for value in physical_clients]
    if (len(physical) != len(set(physical)) or len(physical) > 2
            or any(ip not in ('192.168.50.20', '192.168.50.30') for ip in physical)
            or (physical and role != 'server')):
        raise ValueError('Physical pilot addresses must be the two approved endpoints on server only')
    if internet_uplink is not None and (role != 'server' or not application_policy
            or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}', internet_uplink)
            or internet_uplink in ('lo', 'wg0')):
        raise ValueError('Internet gateway requires server application policy and a distinct uplink')
    own = f"192.168.100.{ADDRESSES[role]}"
    lines = [
        "add table inet vanguard",
        "flush table inet vanguard",
        "table inet vanguard {",
        " chain input {",
        "  type filter hook input priority -10; policy drop;",
        '  iifname "lo" accept',
        # Protect the tunnel address even if a LAN sender routes directly to it.
        '  ip daddr 10.8.0.0/24 iifname != "wg0" counter drop',
        "  ct state invalid drop",
        "  ct state established,related accept",
        f"  ip saddr {management} ip daddr {own} tcp dport 22 counter accept",
        f"  ip saddr {management} ip daddr {own} icmp type echo-request accept",
        # DHCP responses and IPv6 neighbor discovery maintain basic guest networking.
        "  ip saddr 192.168.100.1 udp sport 67 udp dport 68 accept",
        "  meta l4proto ipv6-icmp icmpv6 type { nd-neighbor-solicit, "
        "nd-neighbor-advert, nd-router-advert } ip6 hoplimit 255 accept",
    ]
    if role == "ca":
        lines.append(
            f"  ip saddr {{ 192.168.100.20, 192.168.100.40 }} ip daddr {own} "
            "tcp dport 8080 counter accept"
        )
    elif role == "server":
        extra = ', 192.168.100.60' if windows_client else ''
        extra += ''.join(', ' + ip for ip in physical)
        clients = '{ 10.8.0.2, 10.8.0.4 }' if windows_client else '10.8.0.2'
        lines.extend([
            f"  ip saddr {{ 192.168.100.30, 192.168.100.40, 192.168.100.50{extra} }} "
            f"ip daddr {own} tcp dport 8081 counter accept",
            f"  ip saddr {{ 192.168.100.30, 192.168.100.50{extra} }} ip daddr {own} "
            "udp dport 51820 counter accept",
            f'  iifname "wg0" ip saddr {clients} ip daddr 10.8.0.1 '
            "icmp type echo-request counter accept",
        ])
        if internet_uplink:
            # Roaming managed endpoints are authenticated at the HTTPS/WG boundary;
            # their changing home LAN address is not an identity allowlist.
            lines.extend(['  tcp dport 8081 counter accept',
                          '  udp dport 51820 counter accept'])
    elif role == "admin":
        lines.append(
            f"  ip saddr {management} ip daddr {own} tcp dport 5000 counter accept"
        )
    lines.extend([
        "  counter drop", " }", " chain forward {",
        "  type filter hook forward priority -10; policy drop;", " }", "}",
    ])
    if role == 'server' and application_policy:
        # Dedicated gate precedes established/related. A removed/expired grant
        # cannot continue a previously established application TCP connection.
        gate = [
            ' set application_access {',
            '  type ipv4_addr . ipv4_addr . inet_proto . inet_service; flags timeout;',
            ' }',
            ' chain application_gate {',
            '  iifname "wg0" ip saddr . ip daddr . meta l4proto . tcp dport @application_access counter accept',
            '  counter drop',
            ' }',
            ' chain output {',
            '  type filter hook output priority -10; policy accept;',
            '  oifname "lo" accept',
            '  oifname "wg0" tcp sport 8082 ip daddr . ip saddr . meta l4proto . tcp sport @application_access counter accept',
            '  tcp sport 8082 counter drop',
            ' }',
        ]
        lines[3:3] = gate
        offset = lines.index('  ct state invalid drop')
        lines.insert(offset + 1, '  tcp dport 8082 jump application_gate')
    if internet_uplink:
        # Every packet, including established TCP, must still have a live grant.
        # Never enable flow offloading on this gateway: it bypasses forward hooks.
        denied = ('0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, '
                  '169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, '
                  '192.168.0.0/16, 198.18.0.0/15, 198.51.100.0/24, '
                  '203.0.113.0/24, 224.0.0.0/4, 240.0.0.0/4')
        lines[3:3] = [
            ' set internet_access { type ipv4_addr; flags timeout; }',
            ' set non_internet { type ipv4_addr; flags interval; elements = { ' + denied + ' }; }',
            ' chain internet_nat {',
            '  type nat hook postrouting priority srcnat; policy accept;',
            f'  iifname "wg0" oifname "{internet_uplink}" ip saddr 10.8.0.0/24 masquerade',
            ' }',
        ]
        offset = lines.index('  type filter hook forward priority -10; policy drop;')
        lines[offset + 1:offset + 1] = [
            '  ct state invalid drop',
            '  meta nfproto ipv6 counter drop',
            '  iifname "wg0" ip daddr @non_internet counter drop',
            '  oifname "wg0" ip saddr @non_internet counter drop',
            f'  iifname "wg0" oifname "{internet_uplink}" ip saddr @internet_access meta l4proto {{ tcp, udp, icmp }} counter accept',
            f'  iifname "{internet_uplink}" oifname "wg0" ip daddr @internet_access ct state established,related counter accept',
            '  counter drop',
        ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=ADDRESSES)
    parser.add_argument("--management-ip", required=True)
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument('--windows-client', action='store_true',
                        help='Allow additional Windows client .60 / tunnel .4 on server')
    parser.add_argument('--application-policy', action='store_true',
                        help='Enable default-deny internal-demo TCP/8082 resource gate')
    parser.add_argument('--physical-client', action='append', default=[],
                        help='Generate-only approved pilot source; requires --print-only')
    parser.add_argument('--internet-uplink', help='Opt-in managed IPv4 gateway; generate only')
    args = parser.parse_args()
    if args.internet_uplink and not args.print_only:
        parser.error('Internet rollout requires reviewed backup/recovery; use --print-only')
    if args.physical_client and not args.print_only:
        parser.error('Physical pilot is preparation-only; use --print-only for reviewed rules')
    content = rules(args.role, args.management_ip, args.windows_client, args.application_policy,
                    args.physical_client, args.internet_uplink)
    if args.print_only:
        print(content, end="")
        return
    if os.geteuid() != 0:
        parser.error("Run as root inside the intended lab VM")
    release = Path("/etc/os-release").read_text()
    if 'ID=ubuntu\n' not in release or 'VERSION_ID="22.04"' not in release:
        parser.error("Expected Ubuntu Server 22.04")
    addresses = json.loads(subprocess.check_output(["ip", "-j", "-4", "address", "show"]))
    expected = f"192.168.100.{ADDRESSES[args.role]}"
    if not any(a["local"] == expected for nic in addresses for a in nic["addr_info"]):
        parser.error(f"Expected guest address {expected}; refusing wrong-node firewall")
    if subprocess.run(["nft", "list", "ruleset"], capture_output=True).returncode:
        parser.error("Install nftables before applying the firewall")
    config = Path("/etc/vanguard/firewall.nft")
    config.parent.mkdir(exist_ok=True)
    config.write_text(content)
    os.chmod(config, 0o600)
    subprocess.run(["nft", "--check", "--file", str(config)], check=True)
    unit = Path("/etc/systemd/system/vanguard-firewall.service")
    unit.write_text("""[Unit]
Description=VanGuard lab firewall
DefaultDependencies=no
Wants=network-pre.target
Before=network-pre.target
After=local-fs.target
Conflicts=shutdown.target
Before=shutdown.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft --file /etc/vanguard/firewall.nft
ExecReload=/usr/sbin/nft --file /etc/vanguard/firewall.nft

[Install]
WantedBy=multi-user.target
""")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run([
        "systemd-run", "--unit=vanguard-firewall-rollback", "--on-active=120s",
        "/usr/sbin/nft", "delete", "table", "inet", "vanguard",
    ], check=True)
    subprocess.run(["systemctl", "enable", "vanguard-firewall"], check=True)
    subprocess.run(["systemctl", "restart", "vanguard-firewall"], check=True)
    print("Firewall applied. Confirm fresh SSH access, then stop the rollback timer.")


if __name__ == "__main__":
    main()
