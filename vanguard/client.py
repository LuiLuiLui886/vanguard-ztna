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


def connect(directory, remote, server_key, backend=None, profile=None):
    backend = backend or tunnel_backend()
    with backend.lock() if hasattr(backend, 'lock') else nullcontext():
        return _connect(directory, remote, server_key, backend, profile)


def _connect(directory, remote, server_key, backend, profile=None):
    directory = private_dir(directory)
    wg_key(server_key)
    address = tunnel_ip(json.loads((directory / 'request.json').read_text())['tunnel_ip'])
    backend = backend or tunnel_backend()
    config = directory / (backend.name + '.conf')
    # Only this process owns the tunnel; refuse to overwrite another configuration.
    if config.exists():
        raise Rejected('Tunnel config exists; ensure old tunnel is down before removing it')
    endpoint, routes = '192.168.100.20:51820', '10.8.0.1/32'
    if profile is not None:
        from .profile import validate_profile
        profile = validate_profile(profile)
        if profile['server_public_key'] != server_key or remote.url.rstrip('/') != profile['api_url']:
            raise Rejected('Endpoint profile differs from API or server key')
        endpoint = f"{profile['wireguard_host']}:{profile['wireguard_port']}"
        routes = ', '.join(profile['allowed_ips'])
    backend.preflight()
    admitted = check_admission(admit(directory, remote), address)
    write_private(
        config,
        f"[Interface]\nAddress = {address}/32\n"
        f"PrivateKey = {(directory / 'wg.key').read_text().strip()}\n\n"
        f"[Peer]\nPublicKey = {server_key}\nEndpoint = {endpoint}\n"
        f"AllowedIPs = {routes}\nPersistentKeepalive = 25\n",
    )
    owner = secrets.token_hex(16)
    marker = directory / '.connection.json'
    stop_request = directory / '.disconnect.json'
    write_private(marker, json.dumps({'owner': owner}))
    try:
        backend.up(config)
        print('Admitted; tunnel up. Renewing admission until stopped.', flush=True)
        while True:
            for _ in range(math.ceil(max(1, min(60, (admitted['lease_until'] - time.time()) / 2)))):
                time.sleep(1)
                if stop_request.exists() and json.loads(stop_request.read_text()).get('owner') == owner:
                    return
            admitted = check_admission(admit(directory, remote), address)
    finally:
        # Also clean up a partially successful install. Keep config if cleanup fails
        # so the next invocation refuses rather than taking ownership blindly.
        backend.down(config)
        config.unlink(missing_ok=True)
        stop_request.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)


def disconnect(directory):
    """Ask only the connect process owning this identity to clean up its tunnel."""
    directory = private_dir(directory)
    marker = directory / '.connection.json'
    if not marker.exists():
        raise Rejected('No owned connect process confirmed; inspect any remaining tunnel')
    owner = json.loads(marker.read_text())['owner']
    if not isinstance(owner, str) or len(owner) != 32:
        raise Rejected('Invalid connection ownership marker')
    write_private(directory / '.disconnect.json', json.dumps({'owner': owner}))
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if not marker.exists():
            return {'local_disconnect_confirmed': True, 'server_session_revoked': False}
        if json.loads(marker.read_text()).get('owner') != owner:
            raise Rejected('A newer connection owns the identity; inspect its status')
        time.sleep(.2)
    raise Rejected('Cleanup unconfirmed; config retained. Inspect connect terminal; server session not revoked')


def main():
    parser = argparse.ArgumentParser(description="VanGuard client")
    default_directory = (str(Path(os.environ.get('ProgramData', r'C:\ProgramData'))
                             / 'VanGuard' / 'client') if os.name == 'nt'
                         else '/var/lib/vanguard/client')
    parser.add_argument("--directory", default=default_directory)
    parser.add_argument("--server")
    parser.add_argument("--profile", help="Trusted public endpoint profile JSON")
    parser.add_argument("--trust", default=(str(Path(default_directory) / 'root.crt')
                                            if os.name == 'nt' else '/etc/vanguard/root.crt'))
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--device-id")
    init.add_argument('--tunnel-ip')
    sub.add_parser("admit")
    sub.add_parser("status")
    sub.add_parser("diagnose")
    sub.add_parser("disconnect")
    importer = sub.add_parser("import-bundle")
    importer.add_argument("bundle")
    sub.add_parser('logout')
    login = sub.add_parser('login')
    login.add_argument('--username', required=True)
    connection = sub.add_parser("connect")
    connection.add_argument("--server-key")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        profile = None
        if args.profile:
            from .profile import load_profile
            profile = load_profile(args.profile, args.trust)
            if args.server and args.server.rstrip('/') != profile['api_url']:
                raise Rejected('Do not override API from the trusted profile')
        server = profile['api_url'] if profile else (args.server or 'https://192.168.100.20:8081')
        if args.command == 'import-bundle':
            from .onboarding import import_bundle
            if profile is None:
                raise Rejected('Import requires an independently trusted profile and root')
            print(json.dumps(import_bundle(args.directory, args.bundle, args.trust, profile)))
        elif args.command == 'disconnect':
            print(json.dumps(disconnect(args.directory)))
        elif args.command == 'status':
            directory = Path(args.directory)
            print(json.dumps({'identity_initialized': (directory / 'request.json').is_file(),
                              'certificate_available': (directory / 'device.crt').is_file(),
                              'session_file_present': (directory / 'employee-session.json').is_file(),
                              'tunnel_observation': 'unknown', 'admission_required': True}))
        elif args.command == 'diagnose':
            result = Remote(server, args.trust).call('GET', '/readyz')
            print(json.dumps({'server_readiness': result.get('status', 'unknown'),
                              'wireguard_udp': 'unknown', 'application_access': 'unknown'}))
        elif args.command == "init":
            if profile and (not args.device_id or not args.tunnel_ip):
                raise Rejected('Profile enrollment requires an explicitly allocated device ID and tunnel IP')
            print(initialize(args.directory, args.device_id or 'vm-client', args.tunnel_ip or '10.8.0.2'))
        else:
            remote = Remote(server, args.trust)
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
                key = profile['server_public_key'] if profile else args.server_key
                if not key or (profile and args.server_key and args.server_key != key):
                    raise Rejected('A consistent trusted server public key is required')
                connect(args.directory, remote, key, profile=profile)
    except KeyboardInterrupt:
        pass
    except (Rejected, OSError, ValueError) as exc:
        parser.exit(1, f"VanGuard: {exc}\n")


if __name__ == "__main__":
    main()
