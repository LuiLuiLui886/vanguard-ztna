#!/usr/bin/env python3
"""Exercise real lab services using a disposable identity before client enrollment.

Run only on the authorized five-node lab. The client tunnel must be idle. The test
identity is revoked afterwards; existing production identities are never revoked.
Reports contain no credentials or WireGuard private keys.
"""

import argparse
import json
import os
import shlex
import time
from datetime import datetime, timezone
from pathlib import Path

from deploy_lab import Deployment


class Verification(Deployment):
    def python(self, role, code, data=None):
        return self.ssh(
            role, "sudo /opt/vanguard/venv/bin/python -c " + shlex.quote(code), data
        )

    def dashboard(self, code, data=None):
        program = (
            "from vanguard.admin import create_app\n"
            "d=create_app().extensions['dashboard']\n" + code
        )
        inner = (
            "set -a; . /etc/vanguard/admin.env; set +a; "
            "exec sudo -E -u vanguard /opt/vanguard/venv/bin/python -c "
            + shlex.quote(program)
        )
        return self.ssh("admin", "sudo bash -c " + shlex.quote(inner), data)

    def record(self, name, detail):
        self.results.append({"test": name, "status": "PASS", "detail": detail})
        self.save()
        print(f"PASS {name}: {detail}", flush=True)

    def save(self):
        (self.state / "live-verification.json").write_text(
            json.dumps({"utc": self.started, "device_id": self.name, "results": self.results}, indent=2)
            + "\n"
        )

    def wait_empty(self):
        until = time.monotonic() + 30
        while time.monotonic() < until:
            if not self.ssh("server", "sudo wg show wg0 peers").strip():
                return
            time.sleep(1)
        raise RuntimeError("Server peer still present after 30 seconds")

    def start_tunnel(self):
        key = self.ssh("server", "sudo cat /etc/vanguard/server-wg.pub").decode().strip()
        self.ssh(
            "client",
            "sudo systemctl reset-failed vanguard-lab-check.service 2>/dev/null || true",
        )
        self.ssh(
            "client",
            "sudo systemd-run --unit=vanguard-lab-check --property=RuntimeMaxSec=600 "
            "--property=KillMode=mixed --property=TimeoutStopSec=40 "
            "/opt/vanguard/venv/bin/vanguard-client --directory " + shlex.quote(self.directory)
            + " connect --server-key " + shlex.quote(key),
        )
        self.ssh(
            "client",
            "for i in $(seq 1 30); do ping -c 1 -W 1 10.8.0.1 >/dev/null && exit 0; "
            "sleep 1; done; exit 1",
            timeout=75,
        )

    def stop_tunnel(self):
        self.ssh("client", "sudo systemctl stop vanguard-lab-check.service")

    def run_checks(self):
        self.started = datetime.now(timezone.utc).isoformat()
        self.name = "lab-check-" + str(int(time.time()))
        self.directory = "/var/lib/vanguard/" + self.name
        self.results = []
        self.ssh("client", "! ip link show wg0 >/dev/null 2>&1")
        if self.ssh("server", "sudo wg show wg0 peers").strip():
            raise RuntimeError("Server must have no active peers before this test")
        self.record("clean_start", "Server has zero live peers")
        registered = False
        tunnel_started = False
        ca_stopped = False
        try:
            self.ssh(
                "client",
                "sudo /opt/vanguard/venv/bin/vanguard-client --directory " + self.directory
                + " init --device-id " + self.name,
            )
            request = self.ssh("client", "sudo cat " + self.directory + "/request.json")
            cert = self.dashboard(
                "import json,sys\nb=json.load(sys.stdin)\nd.register(b)\n"
                "sys.stdout.write(d.device(b['device_id'])['certificate'])\n", request
            )
            registered = True
            self.write("client", self.directory + "/device.crt", cert)
            if self.ssh("server", "sudo wg show wg0 peers").strip():
                raise RuntimeError("Registration unexpectedly added a live peer")
            self.record("registry_only", "Certificate issued and bound; zero live peers")
            code = '''import base64,json,sys
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from vanguard.client import identity
from vanguard.pki import fingerprint,proof_message
pem,cert,key,public=identity(sys.stdin.read())
base='https://192.168.100.20:8081'
def post(path, body):
 return requests.post(base+path,json=body,verify='/etc/vanguard/root.crt',timeout=15)
body={'certificate':pem,'wg_public_key':public}
r=post('/api/challenge',{**body,'wg_public_key':base64.b64encode(b'x'*32).decode()})
assert r.status_code==403, ('binding',r.status_code)
c=post('/api/challenge',body); assert c.status_code==200
c=c.json()
bad={**body,'challenge_id':c['challenge_id'],'signature':base64.b64encode(b'invalid').decode()}
assert post('/api/verify',bad).status_code==403
assert post('/api/verify',bad).status_code==403
c=post('/api/challenge',body); assert c.status_code==200
c=c.json()
msg=proof_message(c['challenge_id'],c['nonce'],fingerprint(cert),public,c['tunnel_ip'])
good={**body,'challenge_id':c['challenge_id'],'signature':base64.b64encode(key.sign(msg,ec.ECDSA(hashes.SHA256()))).decode()}
r=post('/api/verify',good); assert r.status_code==200 and r.json()['decision']=='ACCEPT'
assert post('/api/verify',good).status_code==403
print('wrong WG binding, invalid proof, consumed challenge and successful-proof replay rejected; valid proof accepted')
'''
            detail = self.python("client", code, self.directory.encode()).decode().strip()
            self.record("admission_and_replay", detail)
            # Restart must erase the admission granted by the proof test.
            self.ssh("server", "sudo systemctl restart vanguard-server")
            self.wait_empty()
            self.record("api_restart", "Restart clears peer and lease")
            tunnel_started = True
            self.start_tunnel()
            handshakes = self.ssh("server", "sudo wg show wg0 latest-handshakes").decode()
            assert any(int(line.split()[1]) > 0 for line in handshakes.splitlines())
            (self.state / "test-wireguard.txt").write_bytes(self.ssh("server", "sudo wg show wg0"))
            self.record("kernel_handshake_ping", "Nonzero kernel handshake and successful tunnel ping")
            self.ssh("ca", "sudo systemctl stop vanguard-ca")
            ca_stopped = True
            self.wait_empty()
            self.ssh("client", "! ping -c 1 -W 2 10.8.0.1 >/dev/null 2>&1")
            self.record("ca_offline", "Daemon removes live peer; tunnel ping fails")
            self.stop_tunnel()
            tunnel_started = False
            self.ssh("ca", "sudo systemctl start vanguard-ca")
            ca_stopped = False
            tunnel_started = True
            self.start_tunnel()
            self.record("ca_recovery", "Fresh admission restores tunnel after CA returns")
            self.ssh("server", "sudo systemctl stop vanguard-daemon")
            self.ssh(
                "server", "for i in $(seq 1 20); do "
                "if ! systemctl is-active --quiet vanguard-server && "
                "! ip link show wg0 >/dev/null 2>&1; then exit 0; fi; sleep 1; done; exit 1",
            )
            self.record("daemon_stop", "Stopping daemon shuts down server wg0 and admission API")
            self.stop_tunnel()
            tunnel_started = False
            self.ssh("server", "sudo systemctl start vanguard-server")
            tunnel_started = True
            self.start_tunnel()
            # Revoke at CA first to prove the daemon enforces the CRL independently.
            self.dashboard(
                "row=d.device(" + repr(self.name) + ")\n"
                "d.ca.call('POST','/api/ca/revoke',{'serial':row['serial']})\n"
            )
            self.wait_empty()
            self.ssh("client", "! ping -c 1 -W 2 10.8.0.1 >/dev/null 2>&1")
            self.python(
                "client", '''import sys
from vanguard.client import admit
from vanguard.common import Remote,Rejected
try:
 admit(sys.stdin.read(),Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt'))
except Rejected as e:
 assert getattr(e,'upstream_status',None)==403, str(e)
else:
 raise RuntimeError('Revoked identity admitted')
''', self.directory.encode()
            )
            self.record("ca_revocation", "CRL removes active peer and rejects new admission with HTTP 403")
        except Exception as exc:
            self.results.append({"test": "execution", "status": "FAIL", "detail": str(exc)})
            self.save()
            raise
        finally:
            if ca_stopped:
                self.ssh("ca", "sudo systemctl start vanguard-ca")
            if tunnel_started:
                self.stop_tunnel()
            self.ssh("server", "sudo systemctl start vanguard-server")
            if registered:
                self.dashboard("d.revoke(" + repr(self.name) + ")\n")
        self.record("cleanup", "Disposable identity revoked and disabled; production slot available")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    args = parser.parse_args()
    os.umask(0o077)
    Verification(json.loads(args.inventory.read_text()), args.state).run_checks()


if __name__ == "__main__":
    main()
