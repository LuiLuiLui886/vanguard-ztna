#!/usr/bin/env python3
"""Assemble a local deployment kit from verified public inputs; no live installation."""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

from build_endpoint_package import verify_package
from cryptography.hazmat.primitives.serialization import Encoding
from prepare_endpoint_pilot import prepare

from vanguard.pki import load_cert
from vanguard.profile import load_profile

ROOT = Path(__file__).resolve().parents[1]


def build(endpoint, public, wheel, output, expected_endpoint_sha256):
    endpoint, public, wheel, output = map(Path, (endpoint, public, wheel, output))
    if output.exists():
        raise ValueError('Output exists; preserve previous kit')
    if endpoint.is_symlink() or any(p.is_symlink() for p in endpoint.rglob('*')):
        raise ValueError('Endpoint package cannot contain symbolic links')
    raw = (endpoint / 'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_endpoint_sha256:
        raise ValueError('Endpoint manifest fingerprint mismatch')
    manifest = verify_package(endpoint)
    if manifest.get('target') != 'cp313-win_amd64' or manifest.get('version') != '0.1.12':
        raise ValueError('Expected reviewed 0.1.12 Windows candidate')
    profile = load_profile(public / 'profile.json', public / 'root.crt')
    app_name = 'vanguard_ztna-0.1.12-py3-none-any.whl'
    if wheel.name != app_name or hashlib.sha256(wheel.read_bytes()).hexdigest() != manifest['files'].get('wheels/' + app_name):
        raise ValueError('Backend wheel differs from reviewed endpoint application')
    # Re-serialize certificate: never copy arbitrary appended PEM/private input.
    root_pem = load_cert((public / 'root.crt').read_bytes()).public_bytes(Encoding.PEM)
    output.mkdir(parents=True)
    try:
        staging_root = output / 'root-public.crt'
        staging_root.write_bytes(root_pem)
        generated = prepare(staging_root, profile['server_public_key'], output / 'config')
        staging_root.unlink()
        if generated != profile:
            raise ValueError('Kit targets the approved pilot profile only')
        shutil.copytree(endpoint, output / 'windows')
        (output / 'backend').mkdir()
        shutil.copyfile(wheel, output / 'backend' / app_name)
        (output / 'backend/demo').mkdir()
        (output / 'backend/demo/index.html').write_text(
            '<!doctype html><html lang="id"><meta charset="utf-8"><title>VanGuard pilot</title>'
            '<h1>Aplikasi uji VanGuard</h1><p>Halaman publik untuk uji akses melalui tunnel. '
            'Respons ini tidak menggantikan pemeriksaan lease, handshake dan kebijakan.</p></html>\n')
        (output / 'checks').mkdir()
        for name in ('Check-Endpoint.ps1', 'verify_kit.py'):
            shutil.copyfile(ROOT / 'deploy/pilot' / name, output / 'checks' / name)
        shutil.copyfile(ROOT / 'scripts/pilot_preflight.py', output / 'checks/pilot_preflight.py')
        (output / 'docs').mkdir()
        for path in sorted((ROOT / 'docs').iterdir()):
            if path.is_file() and not path.is_symlink() and path.suffix in ('.md', '.html'):
                shutil.copyfile(path, output / 'docs' / path.name)
        (output / 'START_HERE.html').write_text('''<!doctype html><html lang="id"><meta charset="utf-8">
<title>VanGuard — mulai penerapan</title><body><h1>Kit pilot VanGuard</h1>
<p>Kandidat lokal untuk router khusus, PC Windows LAN dan laptop Windows Wi-Fi.
Belum tervalidasi native atau siap produksi.</p>
<ol><li>Verifikasi SHA256 ZIP/manifest dari kanal admin terpisah sebelum menjalankan script.</li>
<li>Buka <a href="docs/INSTALL_REALWORLD.html">panduan langkah pemasangan lengkap</a>.</li>
<li>Jalankan pemeriksa host/endpoint; selesaikan semua FAIL/UNKNOWN dan review manual.</li>
<li>Ikuti urutan backend, PC, laptop, lalu kedua endpoint bersamaan.</li></ol>
<p>Runtime Python/WireGuard diperoleh dari sumber resmi sesuai panduan; tidak termasuk kit.
Jangan mengirim private key, password atau token.</p></body></html>''', encoding='utf-8')
        cases = ('preflight', 'fresh_install', 'uac_cancel', 'wrong_hash', 'path_acl',
                 'enrollment_no_peer', 'login_no_peer', 'admission_handshake', 'http_grant',
                 'deny_without_grant', 'deny_lan_bypass', 'renewal', 'scoped_logout',
                 'revoke_active_tcp', 'expiry', 'reboot', 'wifi_reconnect',
                 'repair_upgrade', 'uninstall_preserve_identity', 'cleanup')
        with (output / 'ACCEPTANCE.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(('device', 'case', 'status', 'observed_at', 'evidence_path', 'notes_no_secrets'))
            for device in ('PC-LAN', 'LAPTOP-WIFI', 'BOTH'):
                for case in cases:
                    writer.writerow((device, case, 'BELUM_DIJALANKAN', '', '', ''))
        (output / 'DEPLOYMENT_STATUS.json').write_text(json.dumps({
            'schema': 1, 'ready_for_production': False, 'status': 'CANDIDATE_REQUIRES_TARGET_VALIDATION',
            'runtime_installers_included': False, 'credentials_included': False,
            'physical_deployment': 'BELUM_DIJALANKAN', 'native_installer': 'BELUM_DIJALANKAN',
            'live_trust_recheck': 'REQUIRED', 'ip_allocation': 'REQUIRED',
            'host_firewall_review': 'REQUIRED'}, indent=2) + '\n')
        # Import generator locally; no application of firewall changes.
        import sys
        sys.path.insert(0, str(ROOT))
        from deploy.firewall import rules
        (output / 'backend/server-firewall.candidate.nft').write_text(rules(
            'server', '192.168.100.1', True, True, ('192.168.50.20', '192.168.50.30')))
        hashes = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(output.rglob('*')) if p.is_file()}
        result = {'schema': 1, 'ready_for_production': False, 'status': 'LOCAL_CANDIDATE',
                  'endpoint_manifest_sha256': expected_endpoint_sha256, 'files': hashes}
        (output / 'kit-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    except Exception:
        # Keep failed preparation evidence; never claim success or erase operator data.
        (output / 'INCOMPLETE.txt').write_text('Build incomplete; do not install. Inspect local build error.\n')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint-package', type=Path, required=True)
    parser.add_argument('--public-profile-dir', type=Path, required=True)
    parser.add_argument('--application-wheel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-endpoint-sha256', required=True)
    args = parser.parse_args()
    result = build(args.endpoint_package, args.public_profile_dir, args.application_wheel,
                   args.output, args.expected_endpoint_sha256)
    print(json.dumps({'status': result['status'], 'files': len(result['files']), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
