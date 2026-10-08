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
import subprocess
from pathlib import Path

ADDRESSES = {"ca": 10, "server": 20, "client": 30, "admin": 40, "attacker": 50}


def rules(role, management):
    management = str(ipaddress.IPv4Address(management))
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
        lines.extend([
            f"  ip saddr {{ 192.168.100.30, 192.168.100.40, 192.168.100.50 }} "
            f"ip daddr {own} tcp dport 8081 counter accept",
            f"  ip saddr {{ 192.168.100.30, 192.168.100.50 }} ip daddr {own} "
            "udp dport 51820 counter accept",
            '  iifname "wg0" ip saddr 10.8.0.2 ip daddr 10.8.0.1 '
            "icmp type echo-request counter accept",
        ])
    elif role == "admin":
        lines.append(
            f"  ip saddr {management} ip daddr {own} tcp dport 5000 counter accept"
        )
    lines.extend([
        "  counter drop", " }", " chain forward {",
        "  type filter hook forward priority -10; policy drop;", " }", "}",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=ADDRESSES)
    parser.add_argument("--management-ip", required=True)
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    content = rules(args.role, args.management_ip)
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
