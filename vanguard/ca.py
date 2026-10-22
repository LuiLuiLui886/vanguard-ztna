"""OpenSSL private CA; all index/serial/CRL mutations hold one filesystem lock."""

import argparse
import hashlib
import ipaddress
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from flask import Response

from .ca_storage import Publication, sync_dir
from .common import (
    Rejected,
    bearer,
    device_name,
    json_body,
    locked,
    make_app,
    private_dir,
    required_secret,
    run,
    write_private,
)
from .pki import check_csr, load_cert


class Authority:
    def __init__(self, directory):
        self.path = private_dir(directory)
        self.config = self.path / "openssl.cnf"
        self.lock = self.path / "ca.lock"

    def openssl(self, *args):
        return run(["openssl", "ca", "-batch", "-config", str(self.config), *args])

    def check_state(self):
        """Check relationships, never reconstruct counters or restore .old files."""
        try:
            root = load_cert((self.path / 'root.crt').read_bytes())
            key = serialization.load_pem_private_key(
                (self.path / 'private/root.key').read_bytes(), None)
            if key.public_key().public_numbers() != root.public_key().public_numbers():
                raise ValueError()
            counters = {}
            for name in ('serial', 'crlnumber'):
                value = (self.path / name).read_text().strip()
                if not re.fullmatch('[0-9A-Fa-f]+', value):
                    raise ValueError()
                counters[name] = int(value, 16)
            indexed, revoked = set(), set()
            for line in (self.path / 'index.txt').read_text().splitlines():
                status, _, _, serial, _, _ = line.split('\t')
                number = int(serial, 16)
                if status not in ('V', 'R', 'E') or number in indexed:
                    raise ValueError()
                cert = load_cert((self.path / 'newcerts' / (serial + '.pem')).read_bytes())
                cert.verify_directly_issued_by(root)
                if cert.serial_number != number or counters['serial'] <= number:
                    raise ValueError()
                indexed.add(number)
                if status == 'R':
                    revoked.add(number)
            for path in (self.path / 'newcerts').glob('*.pem'):
                if load_cert(path.read_bytes()).serial_number not in indexed:
                    raise ValueError()
            crl = x509.load_pem_x509_crl((self.path / 'crl.pem').read_bytes())
            if (not crl.is_signature_valid(root.public_key()) or crl.issuer != root.subject
                    or {entry.serial_number for entry in crl} != revoked
                    or counters['crlnumber'] <= crl.extensions.get_extension_for_class(
                        x509.CRLNumber).value.crl_number):
                raise ValueError()
            for directory in ('issued', 'tls-issued'):
                for path in (self.path / directory).glob('*.crt'):
                    cert = load_cert(path.read_bytes())
                    cert.verify_directly_issued_by(root)
                    if cert.serial_number not in indexed:
                        raise ValueError()
        except Exception as exc:
            raise Rejected('CA state inconsistent; preserve evidence and inspect', 503) from exc

    @contextmanager
    def transaction(self, initialize=False):
        with locked(self.lock):
            publication = Publication(self.path)
            publication.recover()
            if initialize:
                if any(p.name not in ('ca.lock', '.transaction') for p in self.path.iterdir()):
                    raise Rejected('CA already initialized; refusing to overwrite')
            else:
                self.check_state()
            work = Authority(publication.prepare())
            if work.config.exists():
                content = work.config.read_text()
                expected = f'dir = {self.path}\n'
                if expected not in content:
                    raise Rejected('CA configuration needs operator inspection', 503)
                work.config.write_text(content.replace(expected, f'dir = {work.path}\n', 1))
            yield work
            work.check_state()
            work.config.write_text(work.config.read_text().replace(
                f'dir = {work.path}\n', f'dir = {self.path}\n', 1))
            publication.seal()

    def initialize(self):
        with self.transaction(initialize=True) as work:
            work._initialize()

    def _initialize(self):
        with locked(self.lock):
            if self.config.exists():
                raise Rejected("CA already initialized; refusing to overwrite")
            private_dir(self.path / "private")
            private_dir(self.path / "newcerts")
            write_private(self.path / "index.txt", "")
            write_private(self.path / "index.txt.attr", "unique_subject = no\n")
            write_private(self.path / "serial", "1000\n")
            write_private(self.path / "crlnumber", "1000\n")
            write_private(
                self.config,
                f"""[ ca ]
default_ca = vanguard
[ vanguard ]
dir = {self.path}
database = $dir/index.txt
new_certs_dir = $dir/newcerts
certificate = $dir/root.crt
private_key = $dir/private/root.key
serial = $dir/serial
crlnumber = $dir/crlnumber
default_days = 30
default_crl_hours = 1
default_md = sha256
policy = policy
x509_extensions = device
copy_extensions = none
unique_subject = no
crl_extensions = crl_ext
[ policy ]
commonName = supplied
[ device ]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
[ crl_ext ]
authorityKeyIdentifier = keyid:always
""",
            )
            run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-x509",
                    "-newkey",
                    "rsa:3072",
                    "-nodes",
                    "-keyout",
                    str(self.path / "private/root.key"),
                    "-out",
                    str(self.path / "root.crt"),
                    "-days",
                    "3650",
                    "-sha256",
                    "-subj",
                    "/CN=VanGuard Root CA",
                    "-addext",
                    "basicConstraints=critical,CA:true,pathlen:0",
                    "-addext",
                    "keyUsage=critical,keyCertSign,cRLSign",
                    "-addext",
                    "subjectKeyIdentifier=hash",
                ]
            )
            os.chmod(self.path / "private/root.key", 0o600)
            self._crl()

    def _crl(self):
        temporary = self.path / "crl.next.pem"
        self.openssl("-gencrl", "-out", str(temporary))
        temporary.replace(self.path / "crl.pem")
        return (self.path / "crl.pem").read_bytes()

    def crl(self):
        with self.transaction() as work:
            # Freshly issued, signed CRL on every fetch; no stale-cache admission fallback.
            return work._crl()

    def issue(self, name, pem):
        with self.transaction() as work:
            return work._issue(name, pem)

    def _issue(self, name, pem):
        device_name(name)
        parsed = check_csr(pem, name)
        request_hash = hashlib.sha256(parsed.public_bytes(serialization.Encoding.DER)).hexdigest()
        with locked(self.lock), tempfile.TemporaryDirectory(dir=self.path) as tmp:
            issued = private_dir(self.path / "issued") / (request_hash + ".crt")
            if issued.exists():
                certificate = load_cert(issued.read_bytes())
                if (certificate.subject != parsed.subject or certificate.public_key().public_numbers()
                        != parsed.public_key().public_numbers()):
                    raise Rejected('CA issuance cache inconsistent; preserve evidence and inspect', 503)
                return {
                    "certificate": issued.read_text(),
                    "serial": format(certificate.serial_number, "X"),
                }
            csr, cert = Path(tmp) / "device.csr", Path(tmp) / "device.crt"
            csr.write_text(pem)
            self.openssl("-in", str(csr), "-out", str(cert), "-notext")
            certificate = load_cert(cert.read_bytes())
            issued.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
            return {
                "certificate": certificate.public_bytes(serialization.Encoding.PEM).decode(),
                "serial": format(certificate.serial_number, "X"),
            }

    def revoke(self, serial):
        with self.transaction() as work:
            return work._revoke(serial)

    def _revoke(self, serial):
        if not re.fullmatch(r"[0-9A-Fa-f]{1,40}", serial):
            raise Rejected("Invalid serial")
        serial = format(int(serial, 16), "X")
        if len(serial) % 2:
            serial = "0" + serial
        with locked(self.lock):
            cert = self.path / "newcerts" / (serial + ".pem")
            if not cert.exists():
                raise Rejected("Unknown certificate", 404)
            # OpenSSL revoke is not idempotent, so consult its locked index first.
            revoked = any(
                line.split("\t")[0] == "R" and int(line.split("\t")[3], 16) == int(serial, 16)
                for line in (self.path / "index.txt").read_text().splitlines()
            )
            if not revoked:
                self.openssl("-revoke", str(cert), "-crl_reason", "cessationOfOperation")
            self._crl()
        return {"serial": serial, "revoked": True}

    def sign_tls(self, csr_path, ip, output, approved_hosts=()):
        ip = self.tls_host(ip, approved_hosts)
        output = Path(output).resolve()
        if output.exists():
            raise Rejected('Output already exists')
        # Cache signed TLS output in the same commit as index/serial. Retrying
        # after publication but before export cannot issue a second certificate.
        digest = hashlib.sha256(Path(csr_path).read_bytes() + ip.encode()).hexdigest()
        with self.transaction() as work:
            signed = private_dir(work.path / 'tls-issued') / (digest + '.crt')
            if not signed.exists():
                work._sign_tls(csr_path, ip, signed, approved_hosts)
            data = signed.read_bytes()
        with tempfile.NamedTemporaryFile(dir=output.parent) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.link(stream.name, output)  # atomic, exclusive, never overwrite
            sync_dir(output.parent)

    @staticmethod
    def tls_host(value, approved_hosts=()):
        from .profile import host
        value = host(value)
        permitted = {'192.168.100.10', '192.168.100.20', '192.168.100.40'}
        permitted.update(host(name) for name in approved_hosts)
        if value not in permitted:
            raise Rejected('TLS host requires an explicit operator allowlist')
        return value

    def _sign_tls(self, csr_path, ip, output, approved_hosts=()):
        ip = self.tls_host(ip, approved_hosts)
        try:
            ipaddress.IPv4Address(ip)
            san = 'IP:' + ip
        except ValueError:
            san = 'DNS:' + ip
        output = Path(output).resolve()
        if output.exists():
            raise Rejected("Output already exists")
        with locked(self.lock), tempfile.TemporaryDirectory(dir=self.path) as tmp:
            ext = Path(tmp) / "tls.cnf"
            ext.write_text(
                f"[tls]\nbasicConstraints=critical,CA:false\n"
                f"keyUsage=critical,digitalSignature,keyEncipherment\n"
                f"extendedKeyUsage=serverAuth\nsubjectAltName={san}\n"
                "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n"
            )
            self.openssl(
                "-in",
                str(Path(csr_path).resolve()),
                "-out",
                str(output),
                "-notext",
                "-extfile",
                str(ext),
                "-extensions",
                "tls",
                "-days",
                "365",
            )


def create_app(config=None):
    app = make_app(__name__)
    config = config or {}
    authority = Authority(
        config.get("CA_DIR") or os.environ.get("VANGUARD_CA_DIR", "/var/lib/vanguard/ca")
    )
    token = config.get("TOKEN") or required_secret("VANGUARD_CA_TOKEN")
    app.extensions["authority"] = authority

    @app.get("/api/ca/certificate")
    def certificate():
        with locked(authority.lock):
            Publication(authority.path).recover()
            return Response(
                (authority.path / "root.crt").read_bytes(), mimetype="application/x-pem-file"
            )

    @app.get("/api/ca/crl")
    def crl():
        return Response(authority.crl(), mimetype="application/x-pem-file")

    @app.post("/api/ca/issue")
    @bearer(token)
    def issue():
        body = json_body("device_id", "csr")
        return authority.issue(body["device_id"], body["csr"]), 201

    @app.post("/api/ca/revoke")
    @bearer(token)
    def revoke():
        return authority.revoke(json_body("serial")["serial"])

    return app


def main():
    parser = argparse.ArgumentParser(description="VanGuard OpenSSL CA")
    parser.add_argument("--directory", default="/var/lib/vanguard/ca")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    tls = sub.add_parser("sign-tls")
    tls.add_argument("--csr", required=True)
    tls.add_argument("--ip", required=True, help="Service IPv4 or DNS name")
    tls.add_argument("--approved-host", action="append", default=[],
                     help="Explicit operator allowlist for additional service SAN")
    tls.add_argument("--out", required=True)
    args = parser.parse_args()
    authority = Authority(args.directory)
    if args.command == "init":
        authority.initialize()
        print(f"CA initialized: {authority.path / 'root.crt'}")
    else:
        authority.sign_tls(args.csr, args.ip, args.out, args.approved_host)
        print(f"TLS certificate signed: {args.out}")


if __name__ == "__main__":
    main()
