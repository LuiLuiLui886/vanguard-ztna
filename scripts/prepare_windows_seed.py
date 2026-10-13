#!/usr/bin/env python3
"""Prepare a PRIVATE unattended seed and local-only Windows credential inventory.

Only for the NEW blank Windows VM. Never put the output or inventory in Git.
Preparing credentials does not claim an installed OS or verified password.
"""

import argparse
import json
import os
import secrets
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

NS = 'urn:schemas-microsoft-com:unattend'
WCM = 'http://schemas.microsoft.com/WMIConfig/2002/State'
ET.register_namespace('', NS)
ET.register_namespace('wcm', WCM)


def node(parent, tag, text=None, **attrs):
    item = ET.SubElement(parent, '{' + NS + '}' + tag, attrs)
    if text is not None:
        item.text = str(text)
    return item


def component(settings, name):
    return node(settings, 'component', name=name, processorArchitecture='amd64',
                publicKeyToken='31bf3856ad364e35', language='neutral', versionScope='nonSxS')


def unattended(username, password):
    root = ET.Element('{' + NS + '}unattend')
    pe = node(root, 'settings', **{'pass': 'windowsPE'})
    lang = component(pe, 'Microsoft-Windows-International-Core-WinPE')
    node(node(lang, 'SetupUILanguage'), 'UILanguage', 'en-US')
    for key in ('InputLocale', 'SystemLocale', 'UILanguage', 'UserLocale'):
        node(lang, key, 'en-US')
    setup = component(pe, 'Microsoft-Windows-Setup')
    disk = node(node(setup, 'DiskConfiguration'), 'Disk', **{'{' + WCM + '}action': 'add'})
    node(disk, 'DiskID', 0)
    node(disk, 'WillWipeDisk', 'true')
    creates = node(disk, 'CreatePartitions')
    for order, kind, size in ((1, 'EFI', 260), (2, 'MSR', 16), (3, 'Primary', None)):
        part = node(creates, 'CreatePartition', **{'{' + WCM + '}action': 'add'})
        node(part, 'Order', order)
        node(part, 'Type', kind)
        node(part, 'Size' if size else 'Extend', size if size else 'true')
    modifies = node(disk, 'ModifyPartitions')
    for order, number, fs in ((1, 1, 'FAT32'), (2, 3, 'NTFS')):
        part = node(modifies, 'ModifyPartition', **{'{' + WCM + '}action': 'add'})
        node(part, 'Order', order)
        node(part, 'PartitionID', number)
        node(part, 'Format', fs)
        if number == 3:
            node(part, 'Letter', 'C')
            node(part, 'Label', 'Windows')
    install = node(node(setup, 'ImageInstall'), 'OSImage')
    metadata = node(node(install, 'InstallFrom'), 'MetaData', **{'{' + WCM + '}action': 'add'})
    node(metadata, 'Key', '/IMAGE/INDEX')
    node(metadata, 'Value', 1)
    target = node(install, 'InstallTo')
    node(target, 'DiskID', 0)
    node(target, 'PartitionID', 3)
    node(install, 'WillShowUI', 'OnError')
    node(node(setup, 'UserData'), 'AcceptEula', 'true')
    specialize = node(root, 'settings', **{'pass': 'specialize'})
    shell = component(specialize, 'Microsoft-Windows-Shell-Setup')
    node(shell, 'ComputerName', 'VG-WIN-CLIENT')
    node(shell, 'TimeZone', 'SE Asia Standard Time')
    oobe = node(root, 'settings', **{'pass': 'oobeSystem'})
    shell = component(oobe, 'Microsoft-Windows-Shell-Setup')
    settings = node(shell, 'OOBE')
    for key in ('HideEULAPage', 'HideOnlineAccountScreens', 'HideWirelessSetupInOOBE'):
        node(settings, key, 'true')
    node(settings, 'ProtectYourPC', 1)
    accounts = node(node(shell, 'UserAccounts'), 'LocalAccounts')
    account = node(accounts, 'LocalAccount', **{'{' + WCM + '}action': 'add'})
    node(account, 'Name', username)
    node(account, 'DisplayName', 'VanGuard Windows Operator')
    node(account, 'Group', 'Administrators')
    secret = node(account, 'Password')
    node(secret, 'Value', password)
    node(secret, 'PlainText', 'true')
    auto = node(shell, 'AutoLogon')
    node(auto, 'Username', username)
    node(auto, 'Enabled', 'true')
    node(auto, 'LogonCount', 1)
    secret = node(auto, 'Password')
    node(secret, 'Value', password)
    node(secret, 'PlainText', 'true')
    command = node(node(shell, 'FirstLogonCommands'), 'SynchronousCommand',
                   **{'{' + WCM + '}action': 'add'})
    node(command, 'Order', 1)
    node(command, 'Description', 'Configure VanGuard Windows lab client')
    node(command, 'CommandLine', 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '
         '"$v=Get-Volume -FileSystemLabel VGWINSEED; & ($v.DriveLetter+\':\\bootstrap.ps1\')"')
    ET.indent(root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(repository / 'state'):
        parser.error('Seed output must be under the ignored private state directory')
    if output.exists():
        parser.error('Output exists; reuse or inspect existing seed instead of overwriting')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700)
    private = Path('/home/lui/VanGuard-Privat')
    inventory_path, markdown = private / 'kredensial.json', private / 'KREDENSIAL_VANGUARD.md'
    inventory = json.loads(inventory_path.read_text())
    backup = private / ('before-windows-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(mode=0o700)
    for path in (inventory_path, markdown):
        shutil.copyfile(path, backup / path.name)
        (backup / path.name).chmod(0o600)
    entry = inventory['vms'].get('client_windows')
    if entry is None:
        entry = {'username': 'vg' + secrets.token_hex(4),
                 'password': 'Vg!9' + secrets.token_urlsafe(20),
                 'host': '192.168.100.60', 'status': 'PREPARED_NOT_INSTALLED',
                 'console_login_verified': False}
        inventory['vms']['client_windows'] = entry
        inventory['updated_at'] = datetime.now(timezone.utc).isoformat()
        temporary = inventory_path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(inventory, indent=2) + '\n')
        temporary.chmod(0o600)
        temporary.replace(inventory_path)
        with markdown.open('a') as out:
            out.write('\n## VM-CLIENT-WINDOWS — persiapan 13 Oktober 2026\n\n'
                      'Status: PREPARED_NOT_INSTALLED; login belum diverifikasi.\n'
                      'Alamat: 192.168.100.60\n'
                      f'Username: {entry["username"]}\nPassword: {entry["password"]}\n'
                      'Akun console Windows; bukan akun karyawan VPN.\n')
        markdown.chmod(0o600)
    (output / 'Autounattend.xml').write_bytes(unattended(entry['username'], entry['password']))
    shutil.copyfile(repository / 'deploy/windows/bootstrap.ps1', output / 'bootstrap.ps1')
    shutil.copyfile(Path.home() / '.ssh/vanguard_lab_ed25519.pub', output / 'host-access.pub')
    for path in output.iterdir():
        path.chmod(0o600)
    iso = output.with_suffix('.iso')
    if iso.exists():
        parser.error('Seed ISO exists; refusing overwrite')
    subprocess.run(['genisoimage', '-quiet', '-J', '-r', '-V', 'VGWINSEED',
                    '-o', str(iso), str(output)], check=True)
    iso.chmod(0o600)
    print('Private installation seed prepared; credentials saved locally, OS not installed yet.')


if __name__ == '__main__':
    main()
