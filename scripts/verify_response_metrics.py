#!/usr/bin/env python3
"""Measure S-01 application detection/response separately from attacker RTT."""

import argparse
import json
import math
import os
import secrets
import signal
import statistics
import uuid
from datetime import datetime, timezone
from pathlib import Path

from evidence import save_json
from verify_lab import Verification

ATTACK = """import base64,json,os,sys,tempfile,time,requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from vanguard.pki import fingerprint,load_cert,proof_message
p=json.load(sys.stdin)
os.umask(0o077)
def save(status,results):
 with tempfile.NamedTemporaryFile(mode='w',dir='/var/lib/vanguard',delete=False) as out:
  temporary=out.name
  json.dump({'status':status,'samples':results},out);out.flush();os.fsync(out.fileno())
 os.replace(temporary,p['output'])
def post(path,body):
 return requests.post('https://192.168.100.20:8081'+path,json=body,
  verify='/etc/vanguard/root.crt',timeout=15)
r=post('/api/employee/login',p['credentials']); assert r.status_code==200
body={'certificate':p['certificate'],'wg_public_key':p['wg_public_key'],
 'employee_session':r.json()['session_token']}
wrong=ec.generate_private_key(ec.SECP256R1())
results=[]
for number in range(1,11):
 c=post('/api/challenge',body); assert c.status_code==200; c=c.json()
 message=proof_message(c['challenge_id'],c['nonce'],fingerprint(load_cert(p['certificate'])),
  p['wg_public_key'],c['tunnel_ip'])
 request_body={**body,'challenge_id':c['challenge_id'],
  'signature':base64.b64encode(wrong.sign(message,ec.ECDSA(hashes.SHA256()))).decode()}
 started=time.monotonic_ns()
 response=post('/api/verify',request_body)
 elapsed=time.monotonic_ns()-started
 assert response.status_code==403
 results.append({'number':number,'http_status':response.status_code,
  'request_id':response.headers['X-VanGuard-Request-ID'],'attacker_rtt_ns':elapsed})
 # Persist nonsecret evidence after every request, even if a later sample fails.
 save('RUNNING',results)
 time.sleep(1)
save('COMPLETE',results)
print(json.dumps({'employee_login':200,'samples':results}))
"""


def summarize(samples):
    if len(samples) != 10 or len({r['request_id'] for r in samples}) != 10:
        raise ValueError('Ten unique measured attempts are required')
    for sample in samples:
        if sample['http_status'] != 403 or sample['reason'] != 'proof_invalid':
            raise ValueError('Wrong incident population')
        values = [sample[k] for k in ('detect_ns', 'respond_ns', 'total_ns', 'attacker_rtt_ns')]
        if any(not isinstance(v, int) or v < 0 for v in values):
            raise ValueError('Invalid monotonic durations')
        if sample['detect_ns'] + sample['respond_ns'] != sample['total_ns']:
            raise ValueError('Timing boundaries disagree')
    def stats(key):
        values = [r[key] / 1_000_000 for r in samples]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Non-finite metric')
        return {'mean_ms': statistics.mean(values), 'median_ms': statistics.median(values),
                'min_ms': min(values), 'max_ms': max(values), 'stdev_ms': statistics.stdev(values)}
    return {'n': 10, 'MTTD_application': stats('detect_ns'),
            'MTTR_respond_application': stats('respond_ns'),
            'request_to_response_ready': stats('total_ns'), 'attacker_RTT': stats('attacker_rtt_ns')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--state', required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    output = args.state / 'response-metrics.json'
    if output.exists():
        parser.error('Evidence exists; use a new state directory')
    def interrupted(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    v = Verification(json.loads(args.inventory.read_text()), args.state)
    name = 'metrics-' + uuid.uuid4().hex[:12]
    directory = '/var/lib/vanguard/' + name
    remote_output = '/var/lib/vanguard/' + name + '-results.json'
    report = {'status': 'RUNNING', 'utc': datetime.now(timezone.utc).isoformat(),
              'device_id': name, 'directory': directory, 'attacker_output': remote_output}
    def step(name):
        report['current_step'] = name
        save_json(output, report)
    registered = False
    step('registration')
    try:
        before = v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        v.ssh('client', 'sudo /opt/vanguard/venv/bin/vanguard-client --directory ' + directory
              + ' init --device-id ' + name)
        request = json.loads(v.ssh('client', 'sudo cat ' + directory + '/request.json'))
        request['tunnel_ip'] = '10.8.0.3'
        password = secrets.token_urlsafe(24)
        certificate = v.register_identity(request, directory, password=password)
        registered = True
        v.write('client', directory + '/device.crt', certificate)
        assert set(before) == set(v.ssh('server', 'sudo wg show wg0 peers').decode().split())
        step('attacker_series')
        result = json.loads(v.python('attacker', ATTACK, json.dumps({
            'credentials': {'username': 'u-' + name, 'password': password},
            'certificate': certificate.decode(), 'wg_public_key': request['wg_public_key'],
            'output': remote_output,
        }).encode()))
        report['employee_login'] = result['employee_login']
        report['samples'] = result['samples']
        step('correlate_server_audit')
        events = json.loads(v.dashboard(
            "import json\nprint(json.dumps(d.server.call('GET','/api/audit')['events']))\n"))
        timing = [json.loads(e['detail']) for e in events if e['event'] == 'admission_timing']
        for sample in report['samples']:
            matches = [t for t in timing if t['request_id'] == sample['request_id']]
            assert len(matches) == 1, 'Missing/duplicate telemetry correlation'
            entry, = matches
            assert entry['endpoint'] == 'verify' and entry['status'] == 403
            sample.update({k: entry[k] for k in ('detect_ns', 'respond_ns', 'total_ns', 'reason')})
        report['summary'] = summarize(report['samples'])
        assert request['wg_public_key'] not in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        report['attacker_peer_absent'] = True
        step('positive_control')
        v.python('client', "import sys\nfrom vanguard.client import admit\n"
                 "from vanguard.common import Remote\n"
                 "assert admit(sys.stdin.read(),Remote('https://192.168.100.20:8081',"
                 "'/etc/vanguard/root.crt'))['decision']=='ACCEPT'\n", directory.encode())
        assert request['wg_public_key'] in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        report['positive_control'] = 'PASS'
    except BaseException as exc:
        report['status'] = 'INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAIL'
        report['failed_step'], report['error'] = report.get('current_step'), str(exc)
        raise
    finally:
        step('cleanup')
        try:
            if registered:
                v.cleanup_identity(name)
            v.ssh('client', 'ping -c 2 -W 1 10.8.0.1 >/dev/null')
            report['cleanup'] = 'PASS'
        except BaseException as exc:
            report['status'], report['cleanup_error'] = 'FAIL', str(exc)
            raise
        finally:
            save_json(output, report)
    report.update(status='COMPLETE', current_step=None)
    save_json(output, report)
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
