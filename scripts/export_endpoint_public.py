#!/usr/bin/env python3
"""Export verified public endpoint inputs using the host's private SSH inventory."""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding

from vanguard.common import Rejected
from vanguard.pki import fingerprint, load_cert
from vanguard.profile import validate_profile

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    'ca': ('root.crt', 'cat /etc/vanguard/root.crt'),
    'server': ('server-wg.pub', 'sudo -n wg show wg0 public-key'),
    'admin': ('profile.json', 'sudo -n cat /etc/vanguard/endpoint-profile.json'),
}


def fetch(node, command):
    args = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'ConnectTimeout=5']
    if node.get('ssh_config'):
        args += ['-F', node['ssh_config']]
    args += ['-p', str(node.get('port', 22)), node['user'] + '@' + node['host'], command]
    return subprocess.run(args, capture_output=True, check=True, timeout=20).stdout


def export(inventory_path, output_parent):
    inventory = json.loads(Path(inventory_path).read_text())
    data = {}
    for role, (name, command) in COMMANDS.items():
        try:
            data[name] = fetch(inventory[role], command)
        except (OSError, subprocess.SubprocessError, KeyError, TypeError) as exc:
            raise ValueError(f'SSH {role} gagal; periksa VM, inventory dan akses SSH host.') from exc
    try:
        profile = validate_profile(json.loads(data['profile.json']))
        root = load_cert(data['root.crt'])
        digest = fingerprint(root)
        if profile['root_sha256'] != digest:
            raise ValueError('Root mismatch')
        if profile['server_public_key'] != data['server-wg.pub'].decode().strip():
            raise ValueError('Server key mismatch')
    except (Rejected, ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise ValueError('Bahan publik tidak valid atau trust/key tidak cocok; ekspor dibatalkan.') from exc
    data = {'root.crt': root.public_bytes(Encoding.PEM),
            'server-wg.pub': (profile['server_public_key'] + '\n').encode(),
            'profile.json': (json.dumps(profile, indent=2) + '\n').encode()}
    folder = Path(tempfile.mkdtemp(prefix='endpoint-public-', dir=output_parent))
    try:
        for name, content in data.items():
            (folder / name).write_bytes(content)
    except OSError:
        shutil.rmtree(folder)
        raise
    return folder, profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=ROOT / 'state/lab/inventory.json')
    args = parser.parse_args()
    if not args.inventory.is_file():
        parser.exit(1, 'Inventory tidak ditemukan. Jalankan pada host yang sudah disiapkan; '
                    'file privat ini tidak tersedia pada clone GitHub baru atau VM.\n')
    try:
        folder, profile = export(args.inventory, ROOT / 'state')
    except (OSError, ValueError):
        parser.exit(1, 'Ekspor gagal. Periksa SSH ketiga VM, akses sudo noninteraktif, '
                    'inventory dan kesesuaian root/profil/key. Tidak ada folder hasil lengkap.\n')
    print(f'Folder hasil tervalidasi: {folder}')
    print(f"Mode/schema: {profile['schema']}")
    print(f"Fingerprint root: {profile['root_sha256']}")
    print(f"Public key server: {profile['server_public_key']}")
    print('Salin root.crt dan profile.json dari folder ini ke endpoint; simpan nilai trust untuk configure.')


if __name__ == '__main__':
    main()
