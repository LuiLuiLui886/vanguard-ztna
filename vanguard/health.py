"""Bounded, read-only readiness probes. No CRL issuance or peer mutations."""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import requests


def bounded_readiness(role):
    try:
        result = subprocess.run([sys.executable, '-m', 'vanguard.health', role],
                                capture_output=True, timeout=6, check=True)
        data = json.loads(result.stdout)
        if data.get('status') in ('ready', 'not_ready'):
            return data
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return {'status': 'not_ready', 'checks': {'probe': 'unknown'}}


def database_ready(path):
    deadline = time.monotonic() + 0.2
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0.2) as db:
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 100)
        return db.execute('PRAGMA quick_check(1)').fetchone()[0] == 'ok'


def daemon_fresh(directory):
    try:
        record = json.loads((Path(directory) / 'daemon-heartbeat.json').read_text())
        return (record['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                and 0 <= time.monotonic() - record['monotonic'] < 30
                and record['crl_available'] is True)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def dependency_ready(url, trust):
    if not url.startswith('https://'):
        return False
    response = requests.get(url.rstrip('/') + '/readyz', verify=trust,
                            timeout=(0.5, 1), allow_redirects=False)
    return response.status_code == 200 and response.json().get('status') == 'ready'


def probe(role):
    checks = {}
    def inspect(name, action):
        try:
            checks[name] = 'ready' if action() else 'not_ready'
        except Exception:
            checks[name] = 'unknown'

    trust = os.environ.get('VANGUARD_ROOT_CERT', '/etc/vanguard/root.crt')
    if role == 'ca':
        def ca_state():
            import fcntl

            from .ca import Authority
            from .pki import load_cert, validate_crl
            path = Path(os.environ.get('VANGUARD_CA_DIR', '/var/lib/vanguard/ca')).resolve()
            # No Authority constructor: readiness must not mkdir or chmod state.
            authority = object.__new__(Authority)
            authority.path = path
            with open(path / 'ca.lock', 'rb') as lock:
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                if (path / '.transaction/commit.json').exists():
                    return False
                authority.check_state()
                validate_crl(load_cert((path / 'root.crt').read_bytes()),
                             (path / 'crl.pem').read_bytes())
            return True
        inspect('ca_state', ca_state)
    elif role in ('server', 'admin'):
        path = Path(os.environ.get('VANGUARD_' + role.upper() + '_DIR',
                                   '/var/lib/vanguard/' + role)).resolve()
        inspect('database', lambda: database_ready(path / (role + '.db')))
        inspect('ca', lambda: dependency_ready(os.environ.get(
            'VANGUARD_CA_URL', 'https://192.168.100.10:8080'), trust))
        if role == 'server':
            inspect('daemon', lambda: daemon_fresh(path))
            def interface():
                subprocess.run(['wg', 'show', 'wg0', 'peers'], check=True,
                               capture_output=True, timeout=1)
                return True
            inspect('interface', interface)
        else:
            inspect('server', lambda: dependency_ready(os.environ.get(
                'VANGUARD_SERVER_URL', 'https://192.168.100.20:8081'), trust))
    else:
        checks['role'] = 'unknown'
    return {'status': 'ready' if all(v == 'ready' for v in checks.values()) else 'not_ready',
            'checks': checks}


if __name__ == '__main__':
    print(json.dumps(probe(sys.argv[1])))
