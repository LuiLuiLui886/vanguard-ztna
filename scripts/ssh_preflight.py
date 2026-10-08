#!/usr/bin/env python3
"""Read-only SSH inventory check. Uses SSH agent/config and known_hosts only."""

import argparse
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def check(item):
    role, node = item
    for key in ("host", "user"):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", node[key]):
            raise ValueError(f"Invalid {key} for {role}")
    port = int(node.get("port", 22))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port")
    ssh = ["ssh"]
    if node.get("ssh_config"):
        ssh.extend(["-F", str(Path(node["ssh_config"]).resolve())])
    result = subprocess.run(
        ssh
        + [
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "ConnectTimeout=5",
            "-p",
            str(port),
            f"{node['user']}@{node['host']}",
            'hostname; id; . /etc/os-release; printf \'%s %s\\n\' "$ID" "$VERSION_ID"; sudo -n true',
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return {
        "role": role,
        "host": node["host"],
        "ok": result.returncode == 0,
        "details": (result.stdout + result.stderr).strip(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    if set(inventory) != {"ca", "server", "client", "admin", "attacker"}:
        parser.error("Inventory must contain the five VanGuard roles")
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(check, inventory.items()))
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
