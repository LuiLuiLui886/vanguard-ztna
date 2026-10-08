#!/usr/bin/env python3
"""Verify the deployed firewall and existing client's lifecycle without revoking it.

The lease check pauses renewal for 300 seconds; reboot checks briefly interrupt
the lab. Never reboot the workstation running this script. Evidence omits secrets.
"""

import argparse
import json
import os
import shlex
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from deploy_lab import Deployment
from evidence import save_json

REBOOT_ROLES = ("ca", "server", "client", "admin", "attacker")


class Operations(Deployment):
    def python(self, role, code, data=None):
        return self.ssh(role, "sudo /opt/vanguard/venv/bin/python -c " + shlex.quote(code), data)

    def record(self, name, detail):
        self.results.append({"test": name, "status": "PASS", "detail": detail})
        self.save()
        print(f"PASS {name}: {detail}", flush=True)

    def save(self):
        save_json(self.output, {
            "utc": self.started, "updated_utc": datetime.now(timezone.utc).isoformat(),
            "phase": self.phase, "status": self.status, "current_step": self.current_step,
            "results": self.results,
        })

    def until(self, check, seconds=90):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                result = check()
                if result:
                    return result
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
            time.sleep(2)
        raise RuntimeError("Timed out waiting for expected lab state")

    def ping(self):
        return self.ssh("client", "ping -c 2 -W 2 10.8.0.1 >/dev/null && echo ready").strip()

    def rows(self):
        return json.loads(self.python("server", """import sqlite3,json
c=sqlite3.connect('/var/lib/vanguard/server/server.db'); c.row_factory=sqlite3.Row
print(json.dumps([dict(r) for r in c.execute(
 'SELECT device_id,wg_public_key,lease_until FROM devices WHERE enabled=1')]))
"""))

    def removals(self):
        return json.loads(self.python("server", """import sqlite3,json
c=sqlite3.connect('/var/lib/vanguard/server/server.db'); c.row_factory=sqlite3.Row
print(json.dumps([dict(r) for r in c.execute(
 "SELECT * FROM audit WHERE event='peer_removed' ORDER BY id DESC LIMIT 20")]))
"""))

    def matrix(self):
        destinations = [(role, node["host"], 22) for role, node in self.nodes.items()]
        destinations += [("ca", "192.168.100.10", 8080),
                         ("server", "192.168.100.20", 8081),
                         ("admin", "192.168.100.40", 5000)]
        checks = []
        for source in ["host", *self.nodes]:
            targets = []
            for role, host, port in destinations:
                if source == role:
                    continue
                allowed = (
                    (source == "host" and port in (22, 5000))
                    or (port == 8080 and source in ("server", "admin"))
                    or (port == 8081 and source in ("client", "admin", "attacker"))
                )
                targets.append([host, port, allowed])
            code = """import socket,json,sys
from concurrent.futures import ThreadPoolExecutor
def check(target):
 host,port,expected=target
 try:
  with socket.create_connection((host,port),timeout=2): pass
  actual=True
 except OSError: actual=False
 return {'host':host,'port':port,'expected_open':expected,'open':actual}
with ThreadPoolExecutor(max_workers=8) as pool:
 print(json.dumps(list(pool.map(check,json.load(sys.stdin)))))
"""
            if source == "host":
                def check(target):
                    host, port, expected = target
                    try:
                        with socket.create_connection((host, port), timeout=2):
                            pass
                        actual = True
                    except OSError:
                        actual = False
                    return dict(host=host, port=port, expected_open=expected, open=actual)
                with ThreadPoolExecutor(max_workers=8) as pool:
                    outcomes = list(pool.map(check, targets))
            else:
                outcomes = json.loads(self.python(source, code, json.dumps(targets).encode()))
            for result in outcomes:
                result["source"] = source
                checks.append(result)
        (self.state / "firewall-matrix.json").write_text(json.dumps(checks, indent=2) + "\n")
        failures = [c for c in checks if c["open"] != c["expected_open"]]
        if failures:
            raise RuntimeError(f"Firewall matrix mismatch: {failures}")
        self.record("firewall_matrix", f"{len(checks)} TCP allow/deny checks passed")
        for role in self.nodes:
            self.ssh(role, "sudo systemctl is-active --quiet vanguard-firewall && "
                     "sudo systemctl is-enabled --quiet vanguard-firewall")
        self.until(self.ping)
        self.record("firewall_tunnel", "Admitted client handshake and ICMP work through firewall")
        detail = self.ssh("attacker", "/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py")
        (self.state / "attacker-checks-2026-10-08.txt").write_bytes(detail)
        self.record("attacker_api", detail.decode().strip())
        self.ssh("attacker", "sudo ip route add 10.8.0.1/32 via 192.168.100.20")
        try:
            self.ssh("attacker", "! ping -c 2 -W 2 10.8.0.1 >/dev/null 2>&1")
            self.record("tunnel_bypass", "Direct LAN route from attacker cannot reach protected tunnel IP")
        finally:
            self.ssh("attacker", "sudo ip route del 10.8.0.1/32 via 192.168.100.20")

    def lease(self):
        # Obtain a fresh lease immediately, so this measures a full 300 seconds.
        self.ssh("client", "sudo /opt/vanguard/venv/bin/vanguard-client admit")
        # Recover renewal even if the operator terminal closes during the experiment.
        self.ssh("client", "sudo systemd-run --unit=vanguard-renewal-resume --on-active=420s "
                 "/usr/bin/systemctl kill --kill-who=main --signal=SIGCONT vanguard-client")
        self.ssh("client", "sudo systemctl kill --kill-who=main --signal=SIGSTOP vanguard-client")
        started = time.monotonic()
        try:
            row, = self.rows()
            deadline = row["lease_until"]
            key = row["wg_public_key"]
            print("Waiting for the real 300-second lease without renewal…", flush=True)
            while True:
                state = json.loads(self.python("server", """import json,time
from vanguard.server import WireGuard
print(json.dumps({'time':time.time(),'peers':list(WireGuard().peers())}))
"""))
                if key not in state["peers"]:
                    assert state["time"] >= deadline, "Peer disappeared before lease expiry"
                    break
                if state["time"] > deadline + 20:
                    raise RuntimeError("Peer survived beyond lease expiry and polling allowance")
                time.sleep(5)
            self.ssh("client", "! ping -c 1 -W 2 10.8.0.1 >/dev/null 2>&1")
            event = next(e for e in self.removals() if key in e["detail"])
            assert json.loads(event["detail"])["reason"] == "lease_expired"
            self.record("lease_300_seconds", {
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "lease_until": deadline, "removal_timestamp": event["timestamp"],
                "audit_id": event["id"], "renewal_paused": True, "ping_after_expiry": False,
            })
        finally:
            self.ssh("client", "sudo systemctl kill --kill-who=main --signal=SIGCONT vanguard-client")
            self.ssh("client", "sudo systemctl stop vanguard-renewal-resume.timer")
        self.until(self.ping)
        self.record("lease_recovery", "Resuming renewal admits the existing identity and restores ping")

    def reboot(self):
        completed = {r["test"] for r in self.results if r["status"] == "PASS"}
        for role in REBOOT_ROLES:
            if f"reboot_{role}" in completed:
                continue
            self.current_step = f"reboot_{role}"
            self.save()
            old = self.ssh(role, "cat /proc/sys/kernel/random/boot_id").strip()
            self.ssh(role, "sudo systemctl reboot")
            def ready():
                new = self.ssh(role, "cat /proc/sys/kernel/random/boot_id", timeout=15).strip()
                if new == old:
                    return False
                self.ssh(role, "sudo systemctl is-active --quiet vanguard-firewall", timeout=15)
                if role != "attacker":
                    self.ssh(role, f"sudo systemctl is-active --quiet vanguard-{role}", timeout=15)
                return True
            self.until(ready, 180)
            self.until(self.ping, 120)
            self.record(f"reboot_{role}", "Boot ID changed, firewall/service active, main tunnel recovered")

    def run(self, phase, resume=False):
        if resume and phase != "reboot":
            raise ValueError("Only reboot supports resume; other phases require a fresh run")
        self.started = datetime.now(timezone.utc).isoformat()
        self.results = []
        self.output = self.state / f"operations-{phase}.json"
        self.phase, self.status, self.current_step = phase, "RUNNING", phase
        if resume:
            previous = json.loads(self.output.read_text())
            if previous.get("phase", phase) != phase:
                raise ValueError("Evidence phase does not match requested phase")
            self.started = previous["utc"]
            self.results = previous["results"]
        elif self.output.exists():
            raise FileExistsError("Evidence already exists; use a new --state directory")
        self.save()
        try:
            getattr(self, phase)()
        except BaseException as exc:
            self.status = "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAIL"
            self.results.append({"test": phase, "status": "FAIL", "detail": str(exc)})
            self.save()
            raise
        self.status, self.current_step = "COMPLETE", None
        self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("phase", choices=("matrix", "lease", "reboot"))
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    parser.add_argument("--resume", action="store_true", help="Skip recorded successful reboot roles")
    args = parser.parse_args()
    if args.resume and args.phase != "reboot":
        parser.error("--resume is only supported for reboot")
    os.umask(0o077)
    Operations(json.loads(args.inventory.read_text()), args.state).run(args.phase, args.resume)


if __name__ == "__main__":
    main()
