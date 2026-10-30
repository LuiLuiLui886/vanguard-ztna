"""Public, per-device setup contract. No CA secrets or enrollment authorization."""

import argparse
import base64
import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.x509.oid import NameOID

from .common import Rejected, device_name, private_dir, tunnel_ip, write_private
from .profile import load_profile


def load_provision(path, profile, trust):
    source = Path(path)
    if source.stat().st_size > 4096:
        raise Rejected('Provisioning input too large')
    value = json.loads(source.read_text(encoding='utf-8-sig'))
    required = {'schema', 'device_id', 'tunnel_ip', 'root_sha256', 'server_public_key'}
    if not isinstance(value, dict) or set(value) != required or type(value['schema']) is not int or value['schema'] != 1:
        raise Rejected('Invalid public provisioning contract')
    device_name(value['device_id'])
    if not isinstance(value['tunnel_ip'], str):
        raise Rejected('Provisioning tunnel address must be text')
    tunnel_ip(value['tunnel_ip'])
    checked = load_profile(profile, trust)
    if any(value[k] != checked[k] for k in ('root_sha256', 'server_public_key')):
        raise Rejected('Provisioning trust differs from administrator profile')
    return value


def prepare(directory, provision, export):
    """Create once or validate existing keys; export only a verified public request."""
    from .client import local_lock

    directory = private_dir(directory)
    with local_lock(directory.parent / '.provision.lock'):
        return _prepare(directory, provision, export)


def _prepare(directory, provision, export):
    from .client import initialize

    directory = Path(directory)
    if not directory.exists() or not any(directory.iterdir()):
        initialize(directory, provision['device_id'], provision['tunnel_ip'])
    # A partial or conflicting identity is retained for inspection, never regenerated.
    request = json.loads((directory / 'request.json').read_text())
    if any(request.get(k) != provision[k] for k in ('device_id', 'tunnel_ip')):
        raise Rejected('Existing identity differs from allocated device; keys retained')
    key = serialization.load_pem_private_key((directory / 'identity.key').read_bytes(), None)
    csr = x509.load_pem_x509_csr(request['csr'].encode())
    def public(k):
        return k.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    names = csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    if (not csr.is_signature_valid or len(names) != 1 or names[0].value != provision['device_id']
            or public(csr.public_key()) != public(key.public_key())):
        raise Rejected('Existing CSR/key binding differs; preserve identity for inspection')
    wg = x25519.X25519PrivateKey.from_private_bytes(base64.b64decode(
        (directory / 'wg.key').read_text().strip(), validate=True)).public_key()
    if base64.b64encode(wg.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode() != request['wg_public_key']:
        raise Rejected('Existing WireGuard binding differs; keys retained')
    exported = {k: request[k] for k in ('device_id', 'tunnel_ip', 'wg_public_key', 'csr')}
    export = Path(export)
    private_dir(export.parent)
    if export.exists():
        if json.loads(export.read_text()) != exported:
            raise Rejected('Public request already exists with different contents; retained')
    else:
        write_private(export, json.dumps(exported, indent=2) + '\n')
    return {'request_exported': True, 'certificate_present': (directory / 'device.crt').is_file(),
            'admission_required': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provision', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--trust', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--export', required=True)
    args = parser.parse_args()
    try:
        value = load_provision(args.provision, args.profile, args.trust)
        print(json.dumps(prepare(args.directory, value, args.export)))
    except (Rejected, OSError, ValueError, KeyError, TypeError) as exc:
        # Never include a request, key, session, or arbitrary input in setup output.
        raise SystemExit('Endpoint preparation failed; preserve files and inspect allocation/trust.') from exc


if __name__ == '__main__':
    main()
