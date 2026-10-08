#!/usr/bin/env python3
"""Provision the authorized five-VM KVM lab from a verified Ubuntu 22.04 image.

Run as root on the hypervisor. Refuses existing VM names/network/state rather than
overwriting another lab. Does not install application secrets or expose passwords.
"""

import argparse
import json
import os
import pwd
import shutil
import subprocess
from pathlib import Path

NODES = {"ca": 10, "server": 20, "client": 30, "admin": 40, "attacker": 50}


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run as root on the KVM host")
    account = pwd.getpwnam(args.operator)
    qemu = pwd.getpwnam("libvirt-qemu")
    public = args.public_key.read_text().strip()
    if not public.startswith("ssh-ed25519 "):
        parser.error("Supply an Ed25519 SSH public key")
    existing = run("virsh", "-c", "qemu:///system", "list", "--all", "--name").split()
    if any("VM-" + role.upper() in existing for role in NODES):
        parser.error("A VanGuard VM already exists; inspect it before provisioning")
    networks = run("virsh", "-c", "qemu:///system", "net-list", "--all", "--name").split()
    if "vanguard" in networks:
        parser.error("The vanguard network already exists; refusing overwrite")
    base = Path("/var/lib/libvirt/images/vanguard")
    if base.exists():
        parser.error(f"{base} already exists; refusing overwrite")
    base.mkdir(mode=0o755)
    shutil.copyfile(args.image, base / "ubuntu-22.04.img")
    os.chmod(base / "ubuntu-22.04.img", 0o644)
    network = base / "network.xml"
    network.write_text(
        "<network><name>vanguard</name><forward mode='nat'/>"
        "<bridge name='virbr-vg' stp='on' delay='0'/>"
        "<ip address='192.168.100.1' netmask='255.255.255.0'/></network>"
    )
    run("virsh", "-c", "qemu:///system", "net-define", str(network))
    run("virsh", "-c", "qemu:///system", "net-start", "vanguard")
    run("virsh", "-c", "qemu:///system", "net-autostart", "vanguard")
    known_hosts = []
    inventory = {}
    for role, number in NODES.items():
        name = "VM-" + role.upper()
        ip = f"192.168.100.{number}"
        mac = f"52:54:00:76:00:{number:02x}"
        directory = base / role
        directory.mkdir(mode=0o750)
        os.chown(directory, 0, qemu.pw_gid)
        host_key = directory / "ssh_host_ed25519_key"
        run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(host_key))
        host_public = host_key.with_suffix(".pub").read_text().strip()
        known_hosts.append(ip + " " + host_public + "\n")
        cloud = {
            "hostname": name.lower(),
            "manage_etc_hosts": True,
            "ssh_pwauth": False,
            "disable_root": True,
            "ssh_keys": {"ed25519_private": host_key.read_text(), "ed25519_public": host_public},
            "users": [
                {
                    "name": "ubuntu",
                    "groups": "sudo",
                    "shell": "/bin/bash",
                    "sudo": "ALL=(ALL) NOPASSWD:ALL",
                    "lock_passwd": True,
                    "ssh_authorized_keys": [public],
                }
            ],
            "swap": {"filename": "/swapfile", "size": "1G", "maxsize": "1G"},
        }
        (directory / "user-data").write_text("#cloud-config\n" + json.dumps(cloud))
        os.chmod(directory / "user-data", 0o600)
        (directory / "meta-data").write_text(
            json.dumps({"instance-id": name, "local-hostname": name.lower()})
        )
        networking = {
            "version": 2,
            "ethernets": {
                "lab": {
                    "match": {"macaddress": mac},
                    "set-name": "eth0",
                    "dhcp4": False,
                    "addresses": [ip + "/24"],
                    "routes": [{"to": "default", "via": "192.168.100.1"}],
                    "nameservers": {"addresses": ["192.168.100.1"]},
                }
            },
        }
        (directory / "network-config").write_text(json.dumps(networking))
        disk, seed = directory / "disk.qcow2", directory / "seed.img"
        run(
            "qemu-img",
            "create",
            "-f",
            "qcow2",
            "-F",
            "qcow2",
            "-b",
            str(base / "ubuntu-22.04.img"),
            str(disk),
            "10G",
        )
        run(
            "cloud-localds",
            "--network-config=" + str(directory / "network-config"),
            str(seed),
            str(directory / "user-data"),
            str(directory / "meta-data"),
        )
        for path in (disk, seed):
            os.chown(path, qemu.pw_uid, qemu.pw_gid)
            os.chmod(path, 0o600)
        run(
            "virt-install",
            "--connect",
            "qemu:///system",
            "--name",
            name,
            "--memory",
            "768" if role == "server" else "512",
            "--vcpus",
            "1",
            "--cpu",
            "host-passthrough",
            "--import",
            "--os-variant",
            "ubuntu22.04",
            "--disk",
            f"path={disk},bus=virtio,format=qcow2",
            "--disk",
            f"path={seed},device=cdrom",
            "--network",
            f"network=vanguard,model=virtio,mac={mac}",
            "--graphics",
            "none",
            "--noautoconsole",
        )
        inventory[role] = {"host": ip, "user": "ubuntu", "port": 22}
        print(f"Started {name}: {ip}", flush=True)
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chown(args.output, account.pw_uid, account.pw_gid)
    ssh = Path(account.pw_dir) / ".ssh"
    known = ssh / "vanguard_lab_known_hosts"
    config = ssh / "vanguard_lab_config"
    for path in (known, config):
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite SSH file: {path}")
    known.write_text("".join(known_hosts))
    config.write_text(
        "Host " + " ".join(node["host"] for node in inventory.values()) + "\n"
        "  User ubuntu\n  BatchMode yes\n  IdentitiesOnly yes\n"
        f"  IdentityFile {str(args.public_key.resolve())[:-4]}\n"
        f"  UserKnownHostsFile {known}\n  StrictHostKeyChecking yes\n"
    )
    for node in inventory.values():
        node["ssh_config"] = str(config)
    output = args.output / "inventory.json"
    output.write_text(json.dumps(inventory, indent=2) + "\n")
    for path in (known, config, output):
        os.chmod(path, 0o600)
        os.chown(path, account.pw_uid, account.pw_gid)
    print(f"Inventory written to {output}. Host keys pinned from private provisioning seed.")


if __name__ == "__main__":
    main()
