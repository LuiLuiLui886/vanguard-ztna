import argparse
import base64
import getpass
import json
import math
import os
import secrets
import signal
import stat
import tempfile
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.x509.oid import NameOID

from .common import (
    Rejected,
    Remote,
    device_name,
    private_dir,
    run,
    tunnel_ip,
    wg_key,
    write_private,
)
from .pki import fingerprint, load_cert, proof_message


def initialize(directory, name, address='10.8.0.2'):
    address = tunnel_ip(address)
    directory = private_dir(directory)
    device_name(name)
    if any(directory.iterdir()):
        raise Rejected("Identity directory must be empty; keys will not be overwritten")
    identity = ec.generate_private_key(ec.SECP256R1())
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
        .sign(identity, hashes.SHA256())
    )
    wg = x25519.X25519PrivateKey.generate()
    wg_private = base64.b64encode(
        wg.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    ).decode()
    wg_public = base64.b64encode(
        wg.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
    write_private(
        directory / "identity.key",
        identity.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    )
    write_private(directory / "wg.key", wg_private + "\n")
    write_private(
        directory / "request.json",
        json.dumps(
            {
                "device_id": name,
                "csr": csr.public_bytes(serialization.Encoding.PEM).decode(),
                "wg_public_key": wg_public,
                "tunnel_ip": address,
            },
            indent=2,
        ),
    )
    return directory / "request.json"


def identity(directory):
    directory = Path(directory)
    cert_pem = (directory / "device.crt").read_text()
    cert = load_cert(cert_pem)
    key = serialization.load_pem_private_key((directory / "identity.key").read_bytes(), None)
    if (
        not isinstance(key, ec.EllipticCurvePrivateKey)
        or key.public_key().public_numbers() != cert.public_key().public_numbers()
    ):
        raise Rejected("Certificate does not match identity.key")
    wg = x25519.X25519PrivateKey.from_private_bytes(
        base64.b64decode((directory / "wg.key").read_text().strip(), validate=True)
    )
    public = base64.b64encode(
        wg.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
    return cert_pem, cert, key, public


def admit(directory, remote):
    pem, cert, key, public = identity(directory)
    saved_session = json.loads((Path(directory) / 'employee-session.json').read_text())
    if saved_session['expires_at'] <= time.time():
        raise Rejected("Employee session expired; run client login again")
    employee_session = saved_session['session_token']
    challenge = remote.call("POST", "/api/challenge", {
        "certificate": pem, "wg_public_key": public, "employee_session": employee_session,
    })
    message = proof_message(
        challenge["challenge_id"],
        challenge["nonce"],
        fingerprint(cert),
        public,
        challenge["tunnel_ip"],
    )
    if challenge["message"] != message.decode() or challenge["expires_at"] <= time.time():
        raise Rejected("Server challenge does not match client identity")
    signature = base64.b64encode(key.sign(message, ec.ECDSA(hashes.SHA256()))).decode()
    return remote.call(
        "POST",
        "/api/verify",
        {
            "certificate": pem,
            "wg_public_key": public,
            "challenge_id": challenge["challenge_id"],
            "signature": signature,
            "employee_session": employee_session,
        },
    )


def login_employee(directory, remote, username, password):
    directory = private_dir(directory)
    with local_lock(directory / '.session.lock'):
        return _login_employee(directory, remote, username, password)


@contextmanager
def local_lock(path):
    """Nonblocking process lock; persistent lock file is not a secret/session."""
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise Rejected('Client lock unavailable; inspect ownership and path') from exc
    with os.fdopen(fd, 'r+b') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise Rejected('Client lock must be a private regular file')
        if os.name == 'nt':
            import msvcrt
            try:
                # Reading the byte first fails when another Windows handle
                # already locks it. Inspect size without reading locked data.
                if info.st_size == 0:
                    stream.write(b'0')
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise Rejected('Another client operation owns this lock') from exc
        else:
            import fcntl
            if info.st_uid != os.geteuid():
                raise Rejected('Client lock has a different owner')
            os.fchmod(stream.fileno(), 0o600)
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Rejected('Another client operation owns this lock') from exc
        yield


def _login_employee(directory, remote, username, password):
    result = remote.call('POST', '/api/employee/login', {'username': username, 'password': password})
    target = directory / 'employee-session.json'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=directory, delete=False) as out:
            temporary = Path(out.name)
            json.dump(result, out)
            out.flush()
            os.fsync(out.fileno())
        # Windows cannot rename an open NamedTemporaryFile.
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {'username': result['username'], 'expires_at': result['expires_at']}


def logout_employee(directory, remote):
    directory = private_dir(directory)
    with local_lock(directory / '.session.lock'):
        target = directory / 'employee-session.json'
        if not target.exists():
            raise Rejected('Tidak ada token lokal; pencabutan server tidak dapat dikonfirmasi')
        saved = json.loads(target.read_text())
        try:
            result = remote.call('POST', '/api/employee/logout',
                                 {'employee_session': saved['session_token']})
            if result.get('revoked') is not True or result.get('peer_removal_confirmed') is not True:
                raise Rejected('Unexpected logout result')
        except Rejected as exc:
            raise Rejected('Pencabutan server belum terkonfirmasi; token disimpan untuk retry',
                           503) from exc
        target.unlink()
        return {'revoked': True, 'peer_removal_confirmed': True,
                'local_tunnel': 'Proses connect akan cleanup saat renewal berikutnya; '
                                'hentikan dengan Ctrl+C untuk cleanup segera'}


class LinuxTunnel:
    name = 'wg0'

    def __init__(self):
        self.owner = 'vanguard-' + secrets.token_hex(16)
        self.started = False

    def lock(self):
        return local_lock(Path('/run/lock/vanguard-client-wg0.lock'))

    def links(self):
        return json.loads(run(['ip', '-j', 'link', 'show']).stdout)

    def preflight(self):
        if any(link['ifname'] == self.name for link in self.links()):
            raise Rejected('wg0 already exists; ownership is unknown; inspect before connecting')

    def up(self, config):
        run(['wg-quick', 'up', str(config)])
        run(['ip', 'link', 'set', 'dev', self.name, 'alias', self.owner])
        self.started = True

    def down(self, config):
        link = next((item for item in self.links() if item['ifname'] == self.name), None)
        if link is None:
            return
        if not self.started or link.get('ifalias') != self.owner:
            raise Rejected('Tunnel ownership unconfirmed; configuration retained for inspection')
        run(['wg-quick', 'down', str(config)])
        if any(item['ifname'] == self.name for item in self.links()):
            raise Rejected('Tunnel removal unconfirmed; configuration retained')


def tunnel_backend():
    if os.name == 'nt':
        from .windows import WindowsTunnel
        return WindowsTunnel()
    return LinuxTunnel()


def check_admission(result, address):
    if not isinstance(result, dict):
        raise Rejected('Unexpected admission response')
    lease = result.get('lease_until')
    if (result.get('decision') != 'ACCEPT' or result.get('tunnel_ip') != address
            or type(lease) not in (int, float) or not math.isfinite(lease)
            or lease <= time.time()):
        raise Rejected('Unexpected or expired admission response')
    return result


def connect(directory, remote, server_key, backend=None):
    backend = backend or tunnel_backend()
    with backend.lock() if hasattr(backend, 'lock') else nullcontext():
        return _connect(directory, remote, server_key, backend)


def _connect(directory, remote, server_key, backend):
    directory = private_dir(directory)
    wg_key(server_key)
    address = tunnel_ip(json.loads((directory / 'request.json').read_text())['tunnel_ip'])
    backend = backend or tunnel_backend()
    config = directory / (backend.name + '.conf')
    # Only this process owns the tunnel; refuse to overwrite another configuration.
    if config.exists():
        raise Rejected('Tunnel config exists; ensure old tunnel is down before removing it')
    backend.preflight()
    admitted = check_admission(admit(directory, remote), address)
    write_private(
        config,
        f"[Interface]\nAddress = {address}/32\n"
        f"PrivateKey = {(directory / 'wg.key').read_text().strip()}\n\n"
        f"[Peer]\nPublicKey = {server_key}\nEndpoint = 192.168.100.20:51820\n"
        "AllowedIPs = 10.8.0.1/32\nPersistentKeepalive = 25\n",
    )
    try:
        backend.up(config)
        print('Admitted; tunnel up. Renewing admission until stopped.', flush=True)
        while True:
            time.sleep(max(1, min(60, (admitted["lease_until"] - time.time()) / 2)))
            admitted = check_admission(admit(directory, remote), address)
    finally:
        # Also clean up a partially successful install. Keep config if cleanup fails
        # so the next invocation refuses rather than taking ownership blindly.
        backend.down(config)
        config.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="VanGuard client")
    default_directory = (str(Path(os.environ.get('ProgramData', r'C:\ProgramData'))
                             / 'VanGuard' / 'client') if os.name == 'nt'
                         else '/var/lib/vanguard/client')
    parser.add_argument("--directory", default=default_directory)
    parser.add_argument("--server", default="https://192.168.100.20:8081")
    parser.add_argument("--trust", default=(str(Path(default_directory) / 'root.crt')
                                            if os.name == 'nt' else '/etc/vanguard/root.crt'))
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--device-id", default="vm-client")
    init.add_argument('--tunnel-ip', default='10.8.0.2')
    sub.add_parser("admit")
    sub.add_parser('logout')
    login = sub.add_parser('login')
    login.add_argument('--username', required=True)
    connection = sub.add_parser("connect")
    connection.add_argument("--server-key", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "init":
            print(initialize(args.directory, args.device_id, args.tunnel_ip))
        else:
            remote = Remote(args.server, args.trust)
            if args.command == 'login':
                result = login_employee(args.directory, remote, args.username,
                                        getpass.getpass('Employee password: '))
                print(json.dumps(result, indent=2))
            elif args.command == "admit":
                print(json.dumps(admit(args.directory, remote), indent=2))
            elif args.command == 'logout':
                print(json.dumps(logout_employee(args.directory, remote), indent=2))
            else:

                def stop(*_):
                    raise KeyboardInterrupt()

                signal.signal(signal.SIGTERM, stop)
                connect(args.directory, remote, args.server_key)
    except KeyboardInterrupt:
        pass
    except (Rejected, OSError, ValueError) as exc:
        parser.exit(1, f"VanGuard: {exc}\n")


if __name__ == "__main__":
    main()
