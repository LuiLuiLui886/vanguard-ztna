#!/usr/bin/env python3
"""Verify proposal S-01 from VM-ATTACKER with valid disposable employee credentials."""

import argparse
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from evidence import save_json
from verify_lab import Verification

ATTACK = """import base64,json,sys,requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from vanguard.pki import fingerprint,load_cert,proof_message
p=json.load(sys.stdin)
def post(path,body):
 return requests.post('https://192.168.100.20:8081'+path,json=body,
  verify='/etc/vanguard/root.crt',timeout=15)
r=post('/api/employee/login',p['credentials']); assert r.status_code==200
session=r.json()['session_token']
body={'certificate':p['certificate'],'wg_public_key':p['wg_public_key'],
 'employee_session':session}
assert post('/api/challenge',{'employee_session':session,'wg_public_key':p['wg_public_key']}).status_code==400
assert post('/api/challenge',{**body,'wg_public_key':base64.b64encode(b'x'*32).decode()}).status_code==403
c=post('/api/challenge',body); assert c.status_code==200; c=c.json()
message=proof_message(c['challenge_id'],c['nonce'],fingerprint(load_cert(p['certificate'])),
 p['wg_public_key'],c['tunnel_ip'])
wrong=ec.generate_private_key(ec.SECP256R1())
body.update(challenge_id=c['challenge_id'],signature=base64.b64encode(
 wrong.sign(message,ec.ECDSA(hashes.SHA256()))).decode())
assert post('/api/verify',body).status_code==403
assert post('/api/verify',body).status_code==403
print(json.dumps({'employee_login':200,'missing_certificate':400,'wrong_binding':403,
 'copied_certificate_wrong_private_key':403,'replay':403}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    output = args.state / 'employee-verification.json'
    if output.exists():
        parser.error('Evidence already exists; use a new --state directory')
    v = Verification(json.loads(args.inventory.read_text()), args.state)
    name = 's01-' + str(int(time.time())) + '-' + uuid.uuid4().hex[:8]
    directory = '/var/lib/vanguard/' + name
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'RUNNING',
              'device_id': name, 'username': 'u-' + name, 'directory': directory,
              'current_step': 'registration', 'results': []}

    def save():
        save_json(output, report)

    def step(name):
        report['current_step'] = name
        save()

    def record(name, detail):
        report['results'].append({'test': name, 'status': 'PASS', 'detail': detail})
        save()
        print('PASS ' + name, flush=True)

    registered = False
    save()
    try:
        before = v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        v.ssh('client', 'sudo /opt/vanguard/venv/bin/vanguard-client --directory ' + directory
              + ' init --device-id ' + name)
        request = json.loads(v.ssh('client', 'sudo cat ' + directory + '/request.json'))
        request['tunnel_ip'] = '10.8.0.3'
        password = secrets.token_urlsafe(24)
        cert = v.register_identity(request, directory, password=password)
        registered = True
        v.write('client', directory + '/device.crt', cert)
        assert set(before) == set(v.ssh('server', 'sudo wg show wg0 peers').decode().split())
        record('registration', 'Employee/device registration did not add a live peer')
        step('attacker_s01')
        result = json.loads(v.python('attacker', ATTACK, json.dumps({
            'credentials': {'username': 'u-' + name, 'password': password},
            'certificate': cert.decode(), 'wg_public_key': request['wg_public_key'],
        }).encode()))
        assert request['wg_public_key'] not in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        record('S-01', result)
        step('positive_admission')
        v.python('client', "import sys\nfrom vanguard.client import admit\n"
                 "from vanguard.common import Remote\n"
                 "r=admit(sys.stdin.read(),Remote('https://192.168.100.20:8081',"
                 "'/etc/vanguard/root.crt')); assert r['decision']=='ACCEPT'\n", directory.encode())
        assert request['wg_public_key'] in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        record('positive_admission', 'Valid employee session and device proof create kernel peer')
        step('employee_disable')
        started = time.monotonic()
        v.dashboard("d.server.call('POST'," + repr('/api/employees/u-' + name + '/disable') + ",{})\n")
        assert request['wg_public_key'] not in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        record('employee_disable', {'observed_seconds_including_ssh': round(time.monotonic()-started, 3),
                                    'peer_removed': True})
        v.python('client', "import sys\nfrom vanguard.client import admit\n"
                 "from vanguard.common import Remote,Rejected\ntry:\n"
                 " admit(sys.stdin.read(),Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt'))\n"
                 "except Rejected as e:\n assert getattr(e,'upstream_status',None)==403\n"
                 "else: raise RuntimeError('Disabled employee admitted')\n", directory.encode())
        record('disabled_readmission', 'Disabled employee cannot reuse session')
        step('main_tunnel')
        v.ssh('client', 'ping -c 2 -W 2 10.8.0.1 >/dev/null')
        record('main_tunnel', 'Main client still reaches 10.8.0.1')
    except BaseException as exc:
        report['status'] = 'INTERRUPTED' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'FAIL'
        report['error'] = str(exc)
        save()
        raise
    finally:
        step('cleanup')
        try:
            if registered:
                v.cleanup_identity(name)
                record('cleanup', 'Disposable device revoked/disabled and employee disabled')
        except BaseException as exc:
            report['status'] = 'FAIL'
            report['cleanup_error'] = str(exc)
            save()
            raise
    report['status'], report['current_step'] = 'COMPLETE', None
    save()


if __name__ == '__main__':
    main()
