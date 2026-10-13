#!/usr/bin/env python3
"""Attach completed media and start setup only on the recorded NEW blank client.

Never retries an installation automatically. The private marker and report must
be inspected after any interruption; setup completion requires separate guest proof.
"""

import argparse
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from create_windows_client import NAME, ORIGINALS, VOLUME, virsh


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda: source.read(4 * 1024 * 1024), b''):
            result.update(data)
    return result.hexdigest()


def upload(source, name):
    if name in virsh('vol-list', 'default').split():
        raise RuntimeError('Media volume exists; inspect rather than overwrite')
    xml = ET.Element('volume')
    ET.SubElement(xml, 'name').text = name
    ET.SubElement(xml, 'capacity', unit='bytes').text = str(source.stat().st_size)
    target = ET.SubElement(xml, 'target')
    ET.SubElement(target, 'format', type='raw')
    permissions = ET.SubElement(target, 'permissions')
    ET.SubElement(permissions, 'mode').text = '0600'
    temporary = source.parent / (name + '.volume.xml')
    temporary.write_text(ET.tostring(xml, encoding='unicode'))
    virsh('vol-create', 'default', str(temporary))
    virsh('vol-upload', name, str(source), '--pool', 'default')
    return virsh('vol-path', name, '--pool', 'default').strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--media', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    evidence = args.evidence.resolve()
    provision = json.loads((evidence / 'provision/provision.json').read_text())
    if provision.get('status') != 'DEFINED_AWAITING_INSTALL' or provision.get('os_installed'):
        parser.error('Expected a recorded new VM awaiting its first installation')
    marker = evidence / 'installation-started.json'
    if marker.exists():
        parser.error('Installation has already been attempted; inspect guest before any retry')
    if virsh('domstate', NAME).strip() != 'shut off':
        parser.error('New Windows VM must be stopped before first installation')
    for name in ORIGINALS:
        if virsh('domstate', name).strip() != 'shut off':
            parser.error('Install with the five Ubuntu VMs stopped to preserve host RAM')
        content = virsh('dumpxml', name, '--inactive')
        if hashlib.sha256(content.encode()).hexdigest() != provision['original_domains_sha256'][name]:
            parser.error('An original VM definition changed; inspect before install')
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        memory[key] = int(value.strip().split()[0]) * 1024
    if (memory['MemAvailable'] < 2 * 1024**3
            or memory['MemAvailable'] + memory['SwapFree'] < 5 * 1024**3):
        parser.error('Insufficient available host memory; close applications before installing')
    domain = ET.fromstring(virsh('dumpxml', NAME, '--inactive'))
    disks = domain.findall("./devices/disk[@device='disk']/source")
    if len(disks) != 1 or disks[0].get('file') != provision['disk']:
        parser.error('Only the newly created Windows disk may be attached')
    volume = ET.fromstring(virsh('vol-dumpxml', VOLUME, '--pool', 'default'))
    if int(volume.findtext('allocation')) > 5 * 1024 * 1024:
        parser.error('Disk is no longer blank; refusing unattended formatting')
    media = args.media.resolve()
    download = json.loads((media / 'download-complete.json').read_text())
    iso = media / 'windows11-enterprise-eval.iso'
    if (download.get('status') != 'COMPLETE' or iso.stat().st_size != download['size']
            or digest(iso) != download['sha256']):
        parser.error('Downloaded ISO failed length/local checksum verification')
    seed = evidence / 'private-seed.iso'
    if not seed.is_file():
        parser.error('Prepare the private unattended seed first')
    # Claim this installation before mutating any media/domain state.
    report = {'status': 'PREPARING_MEDIA', 'os_installed': False,
              'started_at': time.time(), 'iso_sha256': download['sha256']}
    with marker.open('x') as out:
        json.dump(report, out, indent=2)
    try:
        iso_volume = upload(iso, 'vanguard-windows11-eval.iso')
        seed_volume = upload(seed, 'vanguard-windows-private-seed.iso')
        virsh('change-media', NAME, 'sdb', iso_volume, '--insert', '--config')
        virsh('change-media', NAME, 'sdc', seed_volume, '--insert', '--config')
        virsh('start', NAME)
        report['status'] = 'INSTALLING_GUEST_VALIDATION_PENDING'
        marker.write_text(json.dumps(report, indent=2) + '\n')
        # EFI Windows media asks for a key. Only target the fresh Windows guest.
        for _ in range(8):
            time.sleep(2)
            virsh('send-key', NAME, 'KEY_ENTER')
        virsh('screenshot', NAME, str(evidence / 'installer-start.png'))
        print('Windows installer started; OS completion and client admission remain unverified.')
    except BaseException:
        report['status'] = 'INCOMPLETE_INSPECT_GUEST_BEFORE_RETRY'
        marker.write_text(json.dumps(report, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
