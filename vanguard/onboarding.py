"""Import public enrollment into the original identity, without network access."""

import base64
import io
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .common import Rejected, private_dir
from .pki import fingerprint, load_cert
from .profile import validate_profile


def import_bundle(directory, bundle, trust, profile):
    from .client import local_lock

    directory = private_dir(directory)
    root = load_cert(Path(trust).read_bytes())
    profile = validate_profile(profile)
    if fingerprint(root) != profile['root_sha256']:
        raise Rejected('Trusted root does not match profile')
    path = Path(bundle)
    if path.stat().st_size > 262144:
        raise Rejected('Bundle too large')
    try:
        with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as archive:
            names = archive.namelist()
            if (len(names) != 4 or set(names) != {'manifest.json', 'device.crt', 'root.crt', 'README.txt'}
                    or any(x.file_size > 65536 or x.flag_bits & 1 for x in archive.infolist())):
                raise Rejected('Unexpected bundle members')
            manifest = json.loads(archive.read('manifest.json'))
            pem = archive.read('device.crt')
            cert = load_cert(pem)
            if fingerprint(load_cert(archive.read('root.crt'))) != fingerprint(root):
                raise Rejected('Bundle root differs from trusted root')
        with local_lock(directory / '.session.lock'):
            request = json.loads((directory / 'request.json').read_text())
            key = serialization.load_pem_private_key((directory / 'identity.key').read_bytes(), None)
            if (manifest.get('schema') != 1 or manifest.get('admission_required') is not True
                    or any(manifest.get(k) != request[k] for k in ('device_id', 'wg_public_key', 'tunnel_ip'))
                    or manifest.get('root_sha256') != fingerprint(root)
                    or manifest.get('certificate_sha256') != fingerprint(cert)
                    or validate_profile(manifest.get('profile')) != profile
                    or cert.public_key().public_bytes(serialization.Encoding.DER,
                        serialization.PublicFormat.SubjectPublicKeyInfo) != key.public_key().public_bytes(
                            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)):
                raise Rejected('Bundle/profile does not match original endpoint identity')
            cert.verify_directly_issued_by(root)
            at = datetime.now(timezone.utc)
            if (not root.not_valid_before_utc <= at < root.not_valid_after_utc
                    or not cert.not_valid_before_utc <= at < cert.not_valid_after_utc
                    or cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
                    or not cert.extensions.get_extension_for_class(x509.KeyUsage).value.digital_signature
                    or ExtendedKeyUsageOID.CLIENT_AUTH not in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
                    or ExtendedKeyUsageOID.SERVER_AUTH in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
                    or cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value != request['device_id']):
                raise Rejected('Certificate is not valid for this endpoint')
            # Verify the independent WireGuard private key too, before publishing.
            public = x25519.X25519PrivateKey.from_private_bytes(base64.b64decode(
                (directory / 'wg.key').read_text().strip(), validate=True)).public_key()
            if base64.b64encode(public.public_bytes(serialization.Encoding.Raw,
                    serialization.PublicFormat.Raw)).decode() != request['wg_public_key']:
                raise Rejected('WireGuard key does not match request')
            target = directory / 'device.crt'
            if target.exists():
                if target.read_bytes() != pem:
                    raise Rejected('Existing certificate differs; use replacement identity workflow')
                return {'imported': True, 'unchanged': True, 'admission_required': True}
            # Publish a single public certificate, never replace root/key/session/profile.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=directory, delete=False) as out:
                    temporary = Path(out.name)
                    out.write(pem)
                    out.flush()
                    os.fsync(out.fileno())
                os.link(temporary, target)  # exclusive; concurrent import cannot overwrite
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        return {'imported': True, 'unchanged': False, 'admission_required': True}
    except (ValueError, KeyError, IndexError, InvalidSignature, zipfile.BadZipFile, x509.ExtensionNotFound) as exc:
        raise Rejected('Invalid enrollment bundle') from exc
