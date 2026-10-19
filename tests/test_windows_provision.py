import xml.etree.ElementTree as ET

from scripts.create_windows_client import domain_xml
from scripts.prepare_windows_seed import NS, unattended


def test_windows_vm_is_separate_secure_and_host_local():
    tree = ET.fromstring(domain_xml('/var/lib/libvirt/images/vanguard-windows-client.qcow2'))
    assert tree.findtext('name') == 'VM-CLIENT-WINDOWS'
    assert tree.findtext('memory') == '4096'
    assert tree.find("./os/firmware/feature[@name='secure-boot']").get('enabled') == 'yes'
    assert tree.find("./os/firmware/feature[@name='enrolled-keys']").get('enabled') == 'yes'
    assert tree.find('./devices/tpm/backend').get('version') == '2.0'
    assert tree.find('./devices/interface/mac').get('address') == '52:54:00:76:00:3c'
    assert tree.find('./devices/graphics/listen').get('address') == '127.0.0.1'
    assert len(tree.findall("./devices/disk[@device='disk']")) == 1
    # Synthetic timers require all three dependencies; partial enablement
    # can fail VM startup or leave Windows on expensive emulated timers.
    for feature in ('stimer', 'vpindex', 'synic'):
        assert tree.find('./features/hyperv/' + feature).get('state') == 'on'
    assert tree.find("./clock/timer[@name='hypervclock']").get('present') == 'yes'


def test_private_seed_escapes_values_and_targets_only_new_disk():
    password = 'TEST-only<&not-a-real-password'
    tree = ET.fromstring(unattended('test-operator', password))
    ns = {'u': NS}
    assert tree.find('.//u:LocalAccount/u:Password/u:Value', ns).text == password
    assert tree.find('.//u:LocalAccount/u:Name', ns).text == 'test-operator'
    assert tree.find('.//u:InstallTo/u:DiskID', ns).text == '0'
    assert tree.find('.//u:InstallTo/u:PartitionID', ns).text == '3'
    assert tree.find('.//u:AutoLogon/u:LogonCount', ns).text == '1'
    assert 'VGWINSEED' in tree.find('.//u:CommandLine', ns).text
