"""OpenSSL private CA; all index/serial/CRL mutations hold one filesystem lock."""

import argparse
import hashlib
import ipaddress
import os
import re
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from flask import Response

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

    def initialize(self):
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
        with locked(self.lock):
            # Freshly issued, signed CRL on every fetch; no stale-cache admission fallback.
            return self._crl()

    def issue(self, name, pem):
        device_name(name)
        parsed = check_csr(pem, name)
        request_hash = hashlib.sha256(parsed.public_bytes(serialization.Encoding.DER)).hexdigest()
        with locked(self.lock), tempfile.TemporaryDirectory(dir=self.path) as tmp:
            issued = private_dir(self.path / "issued") / (request_hash + ".crt")
            if issued.exists():
                certificate = load_cert(issued.read_bytes())
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

    def sign_tls(self, csr_path, ip, output):
        ip = str(ipaddress.IPv4Address(ip))
        if ip not in {"192.168.100.10", "192.168.100.20", "192.168.100.40"}:
            raise Rejected("TLS certificate must belong to a VanGuard service VM")
        output = Path(output).resolve()
        if output.exists():
            raise Rejected("Output already exists")
        with locked(self.lock), tempfile.TemporaryDirectory(dir=self.path) as tmp:
            ext = Path(tmp) / "tls.cnf"
            ext.write_text(
                f"[tls]\nbasicConstraints=critical,CA:false\n"
                f"keyUsage=critical,digitalSignature,keyEncipherment\n"
                f"extendedKeyUsage=serverAuth\nsubjectAltName=IP:{ip}\n"
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
    tls.add_argument("--ip", required=True)
    tls.add_argument("--out", required=True)
    args = parser.parse_args()
    authority = Authority(args.directory)
    if args.command == "init":
        authority.initialize()
        print(f"CA initialized: {authority.path / 'root.crt'}")
    else:
        authority.sign_tls(args.csr, args.ip, args.out)
        print(f"TLS certificate signed: {args.out}")


if __name__ == "__main__":
    main()
