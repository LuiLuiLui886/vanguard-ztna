#!/usr/bin/env python3
"""Define one additional Windows client without touching the five Ubuntu VMs.

Default is a reviewable plan. --define creates a sparse disk and a stopped domain;
installation media must be attached separately after verification.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

NAME = 'VM-CLIENT-WINDOWS'
VOLUME = 'vanguard-windows-client.qcow2'
ORIGINALS = ('VM-CA', 'VM-SERVER', 'VM-CLIENT', 'VM-ADMIN', 'VM-ATTACKER')


def virsh(*args):
    return subprocess.check_output(['virsh', '-c', 'qemu:///system', *args], text=True)


def domain_xml(disk):
    root = ET.fromstring(f'''<domain type="kvm">
      <name>{NAME}</name><uuid>{uuid.uuid4()}</uuid>
      <memory unit="MiB">4096</memory><currentMemory unit="MiB">4096</currentMemory>
      <vcpu placement="static">2</vcpu>
      <os firmware="efi"><type arch="x86_64" machine="q35">hvm</type>
        <firmware><feature enabled="yes" name="secure-boot"/>
          <feature enabled="yes" name="enrolled-keys"/></firmware>
        <boot dev="hd"/><boot dev="cdrom"/><bootmenu enable="yes"/>
      </os>
      <features><acpi/><apic/><smm state="on"/>
        <hyperv mode="custom"><relaxed state="on"/><vapic state="on"/>
          <spinlocks state="on" retries="8191"/><vpindex state="on"/>
          <synic state="on"/><stimer state="on"/></hyperv></features>
      <cpu mode="host-passthrough" check="none"/>
      <clock offset="localtime"><timer name="hpet" present="no"/>
        <timer name="hypervclock" present="yes"/></clock>
      <on_poweroff>destroy</on_poweroff><on_reboot>restart</on_reboot>
      <on_crash>destroy</on_crash>
      <devices><emulator>/usr/bin/qemu-system-x86_64</emulator>
        <disk type="file" device="disk"><driver name="qemu" type="qcow2"/>
          <source/><target dev="sda" bus="sata"/></disk>
        <disk type="file" device="cdrom"><driver name="qemu" type="raw"/>
          <target dev="sdb" bus="sata"/><readonly/></disk>
        <disk type="file" device="cdrom"><driver name="qemu" type="raw"/>
          <target dev="sdc" bus="sata"/><readonly/></disk>
        <interface type="network"><mac address="52:54:00:76:00:3c"/>
          <source network="vanguard"/><model type="e1000e"/></interface>
        <controller type="usb" model="qemu-xhci"/>
        <input type="tablet" bus="usb"/>
        <graphics type="vnc" autoport="yes"><listen type="address" address="127.0.0.1"/></graphics>
        <video><model type="vga" primary="yes"/></video>
        <tpm model="tpm-crb"><backend type="emulator" version="2.0"/></tpm>
        <memballoon model="none"/>
      </devices>
    </domain>''')
    root.find('./devices/disk/source').set('file', str(disk))
    ET.indent(root)
    return ET.tostring(root, encoding='unicode') + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--define', action='store_true')
    parser.add_argument('--resume', action='store_true',
                        help='Resume a recorded failed definition using its existing blank disk')
    args = parser.parse_args()
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=True)
    existing = virsh('list', '--all', '--name').split()
    if NAME in existing:
        parser.error('Windows client already exists; inspect checkpoint rather than recreating it')
    if not set(ORIGINALS).issubset(existing):
        parser.error('Expected all five original Ubuntu domains')
    if not shutil.which('swtpm') or not shutil.which('swtpm_setup'):
        parser.error('Install swtpm and swtpm-tools on the host')
    capabilities = ET.fromstring(virsh('domcapabilities', '--machine', 'q35'))
    if not capabilities.findall("./os/enum[@name='firmware']/value[.='efi']"):
        parser.error('Install OVMF firmware on the host')
    network = ET.fromstring(virsh('net-dumpxml', 'vanguard'))
    if network.find("./ip[@address='192.168.100.1']") is None:
        parser.error('Expected the existing VanGuard network')
    pool = ET.fromstring(virsh('pool-dumpxml', 'default'))
    disk = Path(pool.findtext('./target/path')) / VOLUME
    previous = None
    if args.resume:
        previous = json.loads((args.output / 'provision.json').read_text())
        if (not args.define or previous.get('status') != 'INCOMPLETE_INSPECT_BEFORE_RETRY'
                or not previous.get('disk_created') or previous.get('domain_defined')
                or previous.get('disk') != str(disk)):
            parser.error('Resume is only for a recorded disk creation with failed VM definition')
    disk_exists = VOLUME in virsh('vol-list', 'default').split()
    if disk_exists and not previous:
        parser.error('Disk already exists; inspect it before retrying')
    if previous and not disk_exists:
        parser.error('Recorded disk is missing; inspect instead of silently recreating it')
    baseline = {name: virsh('dumpxml', name, '--inactive') for name in ORIGINALS}
    for name, xml in baseline.items():
        if previous:
            if hashlib.sha256(xml.encode()).hexdigest() != previous['original_domains_sha256'][name]:
                parser.error('Original domain changed since failed provisioning')
        else:
            (args.output / (name + '-before.xml')).write_text(xml)
    xml_path = args.output / (NAME + '.xml')
    if previous:
        shutil.copyfile(xml_path, args.output / (NAME + '-failed.xml'))
    xml_path.write_text(domain_xml(disk))
    report = {'status': 'PLANNED', 'name': NAME, 'lan': '192.168.100.60',
              'tunnel': '10.8.0.4', 'disk': str(disk), 'memory_mib': 4096,
              'vcpus': 2, 'capacity_gib': 80, 'os_installed': False,
              'original_domains_sha256': {n: hashlib.sha256(x.encode()).hexdigest()
                                          for n, x in baseline.items()}}
    output = args.output / 'provision.json'

    def record():
        output.write_text(json.dumps(report, indent=2) + '\n')

    record()
    if args.define:
        report['status'] = 'IN_PROGRESS'
        record()
        try:
            if not previous:
                virsh('vol-create-as', 'default', VOLUME, '80G', '--format', 'qcow2')
            report['disk_created'] = True
            record()
            virsh('define', str(xml_path), '--validate')
            report['domain_defined'] = True
            record()
            for name, xml in baseline.items():
                if virsh('dumpxml', name, '--inactive') != xml:
                    raise RuntimeError('Original VM definition changed; inspect private report')
            report['status'] = 'DEFINED_AWAITING_INSTALL'
            report['original_domains_unchanged'] = True
            record()
        except BaseException:
            report['status'] = 'INCOMPLETE_INSPECT_BEFORE_RETRY'
            record()
            raise
    print(json.dumps({k: report[k] for k in ('status', 'name', 'os_installed')}, indent=2))


if __name__ == '__main__':
    main()
