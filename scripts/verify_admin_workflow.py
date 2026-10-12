#!/usr/bin/env python3
"""Exercise admin HTTPS forms on a disposable identity, keeping credentials private."""

import argparse
import io
import json
import os
import re
import secrets
import signal
import time
import uuid
import zipfile
from pathlib import Path

import pyotp
import requests
from evidence import save_json
from verify_lab import Verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--admin-onboarding', required=True, type=Path)
    parser.add_argument('--trust', type=Path, default=Path('state/deployment/root.crt'))
    args = parser.parse_args()
    os.umask(0o077)
    def interrupt(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    v = Verification(json.loads(args.inventory.read_text()), args.state)
    output = args.state / 'admin-workflow.json'
    if output.exists():
        parser.error('Evidence exists; choose a new directory')
    name = 'admin-check-' + uuid.uuid4().hex[:12]
    username, password = 'u-' + name, secrets.token_urlsafe(24)
    directory = '/var/lib/vanguard/' + name
    report = {'status': 'RUNNING', 'device_id': name, 'username': username, 'results': []}
    save_json(output, report)
    session = requests.Session()
    session.verify = str(args.trust.resolve())
    base = 'https://192.168.100.40:5000'
    created = False

    def record(test):
        report['results'].append({'test': test, 'status': 'PASS'})
        save_json(output, report)
        print('PASS ' + test, flush=True)

    def get(path):
        result = session.get(base + path, timeout=35)
        result.raise_for_status()
        return result

    def csrf(path='/'):
        text = get(path).text
        match = re.search(r'name="csrf" value="([^"]+)"', text)
        if not match:
            raise RuntimeError('CSRF form unavailable')
        return match[1]

    def post(path, body, files=None):
        result = session.post(base + path, data={'csrf': csrf(), **body}, files=files,
                              timeout=35, allow_redirects=False)
        if result.status_code != 302:
            raise RuntimeError('Form failed: ' + path)

    try:
        v.python('server', """import sqlite3
c=sqlite3.connect('file:/var/lib/vanguard/server/server.db?mode=ro',uri=True)
assert not c.execute("SELECT 1 FROM devices WHERE enabled=1 AND tunnel_ip='10.8.0.3'").fetchone()
""")
        credentials = json.loads(args.admin_onboarding.read_text())
        totp = pyotp.TOTP(credentials['totp_secret'])
        for attempt in range(2):
            response = session.post(base + '/login', data={
                'csrf': csrf('/login'), 'username': credentials['username'],
                'password': credentials['password'], 'totp': totp.now(),
            }, timeout=35, allow_redirects=False)
            if response.status_code == 302:
                break
            if attempt == 0:
                time.sleep(31 - time.time() % 30)
        else:
            raise RuntimeError('Admin HTTPS login failed')
        page = get('/').text
        assert 'Kesehatan layanan' in page and 'Aktivitas administrasi' in page
        assert '<strong>CA</strong>: Tersedia' in page and '<strong>Server</strong>: Tersedia' in page
        record('admin_totp_login_and_dependency_health')
        # Record intended cleanup identity before the request can reach the server.
        created = True
        post('/employees', {'username': username, 'password': password})
        v.ssh('client', 'sudo /opt/vanguard/venv/bin/vanguard-client --directory '
              + directory + ' init --device-id ' + name)
        request = json.loads(v.ssh('client', 'sudo cat ' + directory + '/request.json'))
        request['tunnel_ip'] = '10.8.0.3'
        post('/devices', {'display_name': 'Perangkat uji admin', 'department': 'Lab',
                         'owner': 'Pengujian otomatis', 'platform': 'Ubuntu 22.04',
                         'employee_username': username},
             {'enrollment': ('request.json', json.dumps(request), 'application/json')})
        certificate = get('/devices/' + name + '/certificate').content
        bundle = get('/devices/' + name + '/bundle')
        with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
            assert set(archive.namelist()) == {'device.crt', 'root.crt', 'manifest.json', 'README.txt'}
            assert archive.read('device.crt') == certificate
            assert json.loads(archive.read('manifest.json'))['device_id'] == name
            for member in archive.namelist():
                data = archive.read(member)
                assert b'PRIVATE KEY-----' not in data and password.encode() not in data
        assert request['wg_public_key'] not in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        assert 'bundle_downloaded' in get('/devices/' + name + '/history').text
        record('registry_only_and_public_bundle_and_history')
        v.write('client', directory + '/device.crt', certificate)
        v.python('client', """import json,sys
from vanguard.client import login_employee,admit
from vanguard.common import Remote
p=json.load(sys.stdin); r=Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt')
login_employee(p['directory'],r,p['username'],p['password'])
assert admit(p['directory'],r)['decision']=='ACCEPT'
""", json.dumps({'directory': directory, 'username': username, 'password': password}).encode())
        assert request['wg_public_key'] in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        record('valid_employee_and_device_admitted')
        post('/devices/' + name + '/revoke', {'reason': 'test_cleanup'})
        row = json.loads(v.dashboard('import json\nr=d.device(' + repr(name) + ')\n'
                                      "print(json.dumps({k:r[k] for k in ('status','revocation_reason','revoked_at')}))"))
        assert row['status'] == 'revoked' and row['revocation_reason'] == 'test_cleanup' and row['revoked_at']
        assert request['wg_public_key'] not in v.ssh('server', 'sudo wg show wg0 peers').decode().split()
        events = json.loads(v.dashboard('import json\nprint(json.dumps(d.history(' + repr(name) + ')))'))
        assert any(e['event'] == 'revocation_completed' and e['actor'] == credentials['username'] for e in events)
        record('ui_revocation_reason_actor_and_peer_removal')
        post('/employees/' + username + '/disable', {})
        record('employee_disabled')
        report['status'] = 'COMPLETE'
    except BaseException as exc:
        report.update(status='INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAIL',
                      error=type(exc).__name__)
        raise
    finally:
        errors = []
        if created:
            try:
                v.cleanup_identity(name)
            except Exception as exc:
                errors.append(type(exc).__name__)
        try:
            v.ssh('client', 'ping -c 2 -W 2 10.8.0.1 >/dev/null')
        except Exception as exc:
            errors.append(type(exc).__name__)
        report['cleanup'] = {'status': 'FAIL' if errors else 'PASS', 'errors': errors}
        if errors:
            report['status'] = 'FAIL'
        save_json(output, report)
        session.close()
        if errors:
            raise RuntimeError('Cleanup failed; inspect private report')


if __name__ == '__main__':
    main()
