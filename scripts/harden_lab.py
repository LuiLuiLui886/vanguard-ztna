#!/usr/bin/env python3
"""Apply the guest firewall matrix to the existing five-node lab with SSH rollback."""

import argparse
import json
import os
from pathlib import Path

from deploy_lab import Deployment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    args = parser.parse_args()
    os.umask(0o077)
    deployment = Deployment(json.loads(args.inventory.read_text()), args.state)
    script = Path(__file__).resolve().parents[1] / "deploy/firewall.py"
    for role in deployment.nodes:
        # Management address is taken from the authenticated connection, never guessed.
        manager = deployment.ssh(role, 'printf "%s" "$SSH_CONNECTION"').decode().split()[0]
        if manager != "192.168.100.1":
            raise RuntimeError(f"Expected lab hypervisor management address, got {manager}")
        existing = deployment.ssh(role, "sudo nft list ruleset")
        backup = args.state / f"firewall-{role}-before.nft"
        if not backup.exists():
            backup.write_bytes(existing)
        deployment.write(role, "/opt/vanguard/firewall.py", script.read_bytes(), 0o755)
        deployment.ssh(
            role, f"sudo python3 /opt/vanguard/firewall.py {role} --management-ip {manager}"
        )
        # A new SSH connection must succeed before disabling the automatic rollback.
        deployment.ssh(role, "sudo systemctl is-active --quiet vanguard-firewall")
        deployment.ssh(role, "sudo systemctl stop vanguard-firewall-rollback.timer")
        (args.state / f"firewall-{role}.nft").write_bytes(
            deployment.ssh(role, "sudo nft list table inet vanguard")
        )
        print(f"{role}: firewall active, fresh SSH access confirmed", flush=True)


if __name__ == "__main__":
    main()
