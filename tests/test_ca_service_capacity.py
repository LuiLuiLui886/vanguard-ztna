"""Exercise the deployed CA thread capacity with real HTTPS, not HTTP stubs."""

import datetime
import ipaddress
import shlex
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from vanguard.health import dependency_ready


def test_ca_tls_probe_can_start_while_four_requests_are_in_flight(tmp_path):
    unit = Path('deploy/systemd/vanguard-ca.service').read_text()
    args = shlex.split(next(line.removeprefix('ExecStart=') for line in unit.splitlines()
                            if line.startswith('ExecStart=')))
    capacity = [item for flag in ('--workers', '--threads')
                for item in (flag, args[args.index(flag) + 1])]
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated-ca-capacity')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(hours=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(
                ipaddress.ip_address('127.0.0.1'))]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .sign(key, hashes.SHA256()))
    trust, private = tmp_path / 'tls.crt', tmp_path / 'tls.key'
    trust.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                         serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))
    private.chmod(0o600)
    (tmp_path / 'capacity_app.py').write_text('''
import time
from pathlib import Path

def app(env, start):
    path = env['PATH_INFO']
    if path.startswith('/hold/'):
        Path('started-' + path.rsplit('/', 1)[-1]).touch()
        deadline = time.monotonic() + 8
        while not Path('release').exists() and time.monotonic() < deadline:
            time.sleep(.01)
    failed = Path('not-ready').exists()
    start('503 Service Unavailable' if failed else '200 OK',
          [('Content-Type', 'application/json')])
    return [b'{"status":"not_ready"}' if failed else b'{"status":"ready"}']
''')
    with socket.socket() as listener, (tmp_path / 'gunicorn.log').open('wb') as log:
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        url = f'https://127.0.0.1:{listener.getsockname()[1]}'
        process = subprocess.Popen(
            [sys.executable, '-m', 'gunicorn', *capacity, '--bind', f'fd://{listener.fileno()}',
             '--chdir', str(tmp_path), '--certfile', str(trust), '--keyfile', str(private),
             'capacity_app:app'], pass_fds=(listener.fileno(),), stdout=log, stderr=log)
        try:
            # Verify TLS and startup before occupying the worker threads.
            deadline = time.monotonic() + 10
            while True:
                try:
                    requests.get(url, verify=str(trust), timeout=(.5, 1)).raise_for_status()
                    break
                except requests.RequestException:
                    assert process.poll() is None
                    if time.monotonic() >= deadline:
                        raise
            with ThreadPoolExecutor(4) as pool:
                held = [pool.submit(requests.get, url + f'/hold/{i}', verify=str(trust),
                                    timeout=(2, 10)) for i in range(4)]
                try:
                    deadline = time.monotonic() + 5
                    while len(list(tmp_path.glob('started-*'))) < 4:
                        assert time.monotonic() < deadline, 'Four holders did not reach the handler'
                        time.sleep(.01)
                    # Uses the production TLS verification and 0.5s connect budget.
                    assert dependency_ready(url, str(trust))
                    (tmp_path / 'not-ready').touch()
                    assert dependency_ready(url, str(trust)) is False
                finally:
                    (tmp_path / 'release').touch()
                for result in held:
                    result.result(timeout=3)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
