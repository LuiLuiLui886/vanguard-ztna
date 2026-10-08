import argparse
import base64
import json
import os
import signal
import time
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.x509.oid import NameOID

from .common import Rejected, Remote, device_name, private_dir, run, wg_key, write_private
from .pki import fingerprint, load_cert, proof_message


def initialize(directory, name):
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
                "tunnel_ip": "10.8.0.2",
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
    challenge = remote.call("POST", "/api/challenge", {"certificate": pem, "wg_public_key": public})
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
        },
    )


def connect(directory, remote, server_key):
    directory = Path(directory).resolve()
    wg_key(server_key)
    config = directory / "wg0.conf"
    # Only this process owns wg0; refuse to overwrite another configuration.
    if config.exists():
        raise Rejected("wg0.conf exists; ensure old tunnel is down before removing it")
    admitted = admit(directory, remote)
    if admitted["decision"] != "ACCEPT" or admitted["tunnel_ip"] != "10.8.0.2":
        raise Rejected("Unexpected admission response")
    write_private(
        config,
        f"[Interface]\nAddress = 10.8.0.2/24\n"
        f"PrivateKey = {(directory / 'wg.key').read_text().strip()}\n\n"
        f"[Peer]\nPublicKey = {server_key}\nEndpoint = 192.168.100.20:51820\n"
        "AllowedIPs = 10.8.0.1/32\nPersistentKeepalive = 25\n",
    )
    started = False
    try:
        run(["wg-quick", "up", str(config)])
        started = True
        print("Admitted; wg0 up. Renewing admission until stopped.", flush=True)
        while True:
            time.sleep(max(1, min(60, (admitted["lease_until"] - time.time()) / 2)))
            admitted = admit(directory, remote)
    finally:
        if started:
            run(["wg-quick", "down", str(config)])
        config.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="VanGuard client")
    parser.add_argument("--directory", default="/var/lib/vanguard/client")
    parser.add_argument("--server", default="https://192.168.100.20:8081")
    parser.add_argument("--trust", default="/etc/vanguard/root.crt")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--device-id", default="vm-client")
    sub.add_parser("admit")
    connection = sub.add_parser("connect")
    connection.add_argument("--server-key", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "init":
            print(initialize(args.directory, args.device_id))
        else:
            remote = Remote(args.server, args.trust)
            if args.command == "admit":
                print(json.dumps(admit(args.directory, remote), indent=2))
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
