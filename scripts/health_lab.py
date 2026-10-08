#!/usr/bin/env python3
"""Read-only service/tunnel observation with durable evidence after every sample."""

import argparse
import json
import os
import shlex
import time
from datetime import datetime, timezone
from pathlib import Path

from deploy_lab import Deployment
from evidence import save_json

SERVER_PROBE = """import json,sqlite3,subprocess,time
c=sqlite3.connect('file:/var/lib/vanguard/server/server.db?mode=ro',uri=True)
c.row_factory=sqlite3.Row
rows=[dict(r) for r in c.execute(
 'SELECT device_id,wg_public_key,tunnel_ip,enabled,lease_until FROM devices WHERE enabled=1')]
def wg(field):
 return subprocess.check_output(['wg','show','wg0',field],text=True).strip()
events=[dict(r) for r in c.execute(
 "SELECT id,timestamp,device_id,detail FROM audit WHERE event='peer_removed' ORDER BY id DESC LIMIT 20")]
print(json.dumps({'time':time.time(),'devices':rows,'peers':wg('peers').split(),
 'allowed_ips':wg('allowed-ips'),'handshakes':wg('latest-handshakes'),'removals':events}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--interval", type=float, default=10)
    args = parser.parse_args()
    if args.samples < 1 or args.interval < 1:
        parser.error("samples must be positive and interval must be at least one second")
    os.umask(0o077)
    deployment = Deployment(json.loads(args.inventory.read_text()), args.state)
    output = args.state / "health.json"
    if output.exists():
        parser.error("health.json exists; choose a new --state directory")
    started = time.time()
    report = {"utc": datetime.now(timezone.utc).isoformat(), "status": "RUNNING", "samples": []}
    save_json(output, report)
    try:
        for number in range(args.samples):
            sample = {"utc": datetime.now(timezone.utc).isoformat(), "status": "RUNNING"}
            report["samples"].append(sample)
            save_json(output, report)
            for role in deployment.nodes:
                units = ["vanguard-firewall", "ssh" if role == "attacker" else "vanguard-" + role]
                if role == "server":
                    units += ["vanguard-daemon", "wg-quick@wg0"]
                states = deployment.ssh(
                    role, "sudo systemctl is-active " + " ".join(units), timeout=20
                ).decode().splitlines()
                if states != ["active"] * len(units):
                    raise RuntimeError(f"Inactive service on {role}: {dict(zip(units, states))}")
            sample["server"] = json.loads(deployment.ssh(
                "server", "sudo /opt/vanguard/venv/bin/python -c " + shlex.quote(SERVER_PROBE),
                timeout=20,
            ))
            server = sample["server"]
            main = [r for r in server["devices"] if r["device_id"] == "vm-client"]
            if len(main) != 1 or main[0]["wg_public_key"] not in server["peers"]:
                raise RuntimeError("Main client is missing from enabled registry/live peers")
            if main[0]["lease_until"] <= server["time"]:
                raise RuntimeError("Main client lease expired")
            expected = main[0]["wg_public_key"] + "\t10.8.0.2/32"
            if expected not in server["allowed_ips"].splitlines():
                raise RuntimeError("Main client's allowed IP differs from lab binding")
            sample["ping"] = deployment.ssh("client", "ping -c 2 -W 2 10.8.0.1", timeout=15).decode()
            sample["removals_since_start"] = [e for e in server["removals"]
                                               if e["timestamp"] >= started]
            if sample["removals_since_start"]:
                raise RuntimeError("Peer removal observed during stability window; inspect evidence")
            sample["status"] = "PASS"
            save_json(output, report)
            print(f"PASS sample {number + 1}/{args.samples}: services, lease, peers and ping", flush=True)
            if number + 1 < args.samples:
                time.sleep(args.interval)
    except BaseException as exc:
        report["status"] = "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAIL"
        report["error"] = str(exc)
        if report["samples"]:
            report["samples"][-1]["status"] = report["status"]
        save_json(output, report)
        raise
    report["status"] = "COMPLETE"
    report["elapsed_seconds"] = round(time.time() - started, 2)
    save_json(output, report)


if __name__ == "__main__":
    main()
