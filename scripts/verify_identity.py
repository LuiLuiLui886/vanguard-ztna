#!/usr/bin/env python3
"""Verify registration, admission, replay and CA revocation beside the main client.

Uses a disposable identity at 10.8.0.3, without starting another client interface.
The existing vm-client at 10.8.0.2 is never disabled or revoked by this script.
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from evidence import save_json
from verify_lab import Verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    args = parser.parse_args()
    os.umask(0o077)
    v = Verification(json.loads(args.inventory.read_text()), args.state)
    name = "final-check-" + str(int(time.time())) + "-" + uuid.uuid4().hex[:8]
    directory = "/var/lib/vanguard/" + name
    output = args.state / (name + ".json")
    report = {"utc": datetime.now(timezone.utc).isoformat(), "device_id": name,
              "directory": directory, "status": "RUNNING", "current_step": "registration",
              "results": []}
    def save():
        report["updated_utc"] = datetime.now(timezone.utc).isoformat()
        save_json(output, report)
    def record(test, detail):
        report["results"].append({"test": test, "status": "PASS", "detail": detail})
        save()
        print(f"PASS {test}: {detail}", flush=True)
    save()
    registered = False
    try:
        v.ssh("client", "sudo /opt/vanguard/venv/bin/vanguard-client --directory " + directory
              + " init --device-id " + name)
        request = json.loads(v.ssh("client", "sudo cat " + directory + "/request.json"))
        request["tunnel_ip"] = "10.8.0.3"
        key = request["wg_public_key"]
        certificate = v.dashboard(
            "import json,sys\nb=json.load(sys.stdin)\nd.register(b)\n"
            "sys.stdout.write(d.device(b['device_id'])['certificate'])\n",
            json.dumps(request).encode(),
        )
        registered = True
        v.write("client", directory + "/device.crt", certificate)
        assert key not in v.ssh("server", "sudo wg show wg0 peers").decode()
        record("registration", "Disposable identity registered at 10.8.0.3 without a live peer")
        report["current_step"] = "admission_proof_replay"
        save()
        program = """import base64,sys,requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from vanguard.client import identity
from vanguard.pki import fingerprint,proof_message
pem,cert,key,public=identity(sys.stdin.read())
def post(path,body):
 return requests.post('https://192.168.100.20:8081'+path,json=body,
  verify='/etc/vanguard/root.crt',timeout=15)
body={'certificate':pem,'wg_public_key':public}
assert post('/api/challenge',{**body,'wg_public_key':base64.b64encode(b'x'*32).decode()}).status_code==403
c=post('/api/challenge',body); assert c.status_code==200; c=c.json()
bad={**body,'challenge_id':c['challenge_id'],'signature':base64.b64encode(b'invalid').decode()}
assert post('/api/verify',bad).status_code==403
assert post('/api/verify',bad).status_code==403
c=post('/api/challenge',body); assert c.status_code==200; c=c.json()
assert c['tunnel_ip']=='10.8.0.3'
msg=proof_message(c['challenge_id'],c['nonce'],fingerprint(cert),public,c['tunnel_ip'])
good={**body,'challenge_id':c['challenge_id'],
 'signature':base64.b64encode(key.sign(msg,ec.ECDSA(hashes.SHA256()))).decode()}
r=post('/api/verify',good); assert r.status_code==200 and r.json()['decision']=='ACCEPT'
assert post('/api/verify',good).status_code==403
"""
        v.python("client", program, directory.encode())
        assert key in v.ssh("server", "sudo wg show wg0 peers").decode()
        record("admission_proof_replay", "Wrong binding/proof and replay rejected; valid proof creates kernel peer")
        report["current_step"] = "revocation"
        save()
        v.dashboard("row=d.device(" + repr(name) + ")\n"
                    "d.ca.call('POST','/api/ca/revoke',{'serial':row['serial']})\n")
        deadline = time.monotonic() + 30
        while key in v.ssh("server", "sudo wg show wg0 peers").decode():
            if time.monotonic() >= deadline:
                raise RuntimeError("Revoked peer not removed")
            time.sleep(1)
        events = json.loads(v.python("server", """import sqlite3,json
c=sqlite3.connect('/var/lib/vanguard/server/server.db'); c.row_factory=sqlite3.Row
print(json.dumps([dict(r) for r in c.execute("SELECT * FROM audit WHERE event='peer_removed' ORDER BY id DESC LIMIT 10")]))
"""))
        event = next(e for e in events if e["device_id"] == name)
        assert json.loads(event["detail"])["reason"] == "certificate_revoked"
        v.python("client", """import sys
from vanguard.client import admit
from vanguard.common import Remote,Rejected
try:
 admit(sys.stdin.read(),Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt'))
except Rejected as e:
 assert getattr(e,'upstream_status',None)==403
else: raise RuntimeError('Revoked identity admitted')
""", directory.encode())
        v.ssh("client", "ping -c 3 -W 2 10.8.0.1 >/dev/null")
        record("revocation", "CA-only revocation removes kernel peer with certificate_revoked audit; readmission denied; main tunnel survives")
    except BaseException as exc:
        report["status"] = "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAIL"
        report["results"].append({"test": "execution", "status": "FAIL", "detail": str(exc)})
        save()
        raise
    finally:
        report["current_step"] = "cleanup"
        save()
        try:
            if registered:
                v.dashboard("d.revoke(" + repr(name) + ")\n")
                record("cleanup", "Disposable identity revoked and disabled; main identity unchanged")
        except BaseException as exc:
            report["status"] = "FAIL"
            report["results"].append({"test": "cleanup", "status": "FAIL", "detail": str(exc)})
            raise
        finally:
            save()
    report["status"], report["current_step"] = "COMPLETE", None
    save()


if __name__ == "__main__":
    main()
