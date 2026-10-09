#!/usr/bin/env python3
"""Deploy VanGuard onto five existing, SSH-authenticated Ubuntu 22.04 VMs.

Private application keys stay on their VM. Generated admin onboarding is written
only to a private local file. Never print tokens, passwords or TOTP secrets.
"""

import argparse
import hashlib
import json
import os
import secrets
import shlex
import subprocess
from pathlib import Path

from evidence import save_json
from ssh_preflight import check

ROLES = ("ca", "server", "client", "admin", "attacker")


class Deployment:
    def __init__(self, inventory, state):
        self.nodes = inventory
        self.state = state
        state.mkdir(parents=True, exist_ok=True, mode=0o700)

    def ssh(self, role, command, data=None, timeout=1800):
        node = self.nodes[role]
        args = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "ConnectTimeout=10",
        ]
        if node.get("ssh_config"):
            args += ["-F", node["ssh_config"]]
        args += ["-p", str(node.get("port", 22)), f"{node['user']}@{node['host']}", command]
        result = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
        if result.returncode:
            # Command arguments can contain only paths/code here; secrets travel on stdin.
            raise RuntimeError(
                f"{role}: remote operation failed: {result.stderr.decode(errors='replace')[-2000:]}"
            )
        return result.stdout

    def write(self, role, path, data, mode=0o600, owner=None):
        code = (
            "import os,sys,pathlib,shutil; "
            f"p=pathlib.Path({path!r}); p.parent.mkdir(parents=True,exist_ok=True); "
            "p.write_bytes(sys.stdin.buffer.read()); "
            f"os.chmod(p,{mode}); "
        )
        if owner:
            code += f"shutil.chown(p,user={owner!r},group={owner!r}); "
        self.ssh(role, "sudo python3 -c " + shlex.quote(code), data)

    def employee_access(self, username='employee-lab', name='vm-client',
                        directory='/var/lib/vanguard/client'):
        """Bootstrap an explicit lab employee; retain credentials only in private state."""
        path = self.state / 'employee-onboarding.json'
        if path.exists():
            credentials = json.loads(path.read_text())
            if credentials['username'] != username:
                raise RuntimeError('Employee onboarding belongs to a different username')
        else:
            credentials = {'username': username, 'password': secrets.token_urlsafe(24)}
            save_json(path, credentials)
        code = """import json,sys
from vanguard.admin import create_app
d=create_app().extensions['dashboard']
p=json.load(sys.stdin)
employees=d.server.call('GET','/api/employees')['employees']
if not any(e['username']==p['username'] for e in employees):
 d.server.call('POST','/api/employees',{'username':p['username'],'password':p['password']})
d.bind_employee(p['device_id'],p['username'])
"""
        inner = ('set -a; . /etc/vanguard/admin.env; set +a; '
                 'exec sudo -E -u vanguard /opt/vanguard/venv/bin/python -c ' + shlex.quote(code))
        self.ssh('admin', 'sudo bash -c ' + shlex.quote(inner),
                 json.dumps({**credentials, 'device_id': name}).encode())
        code = """import json,sys
from vanguard.client import login_employee
from vanguard.common import Remote
p=json.load(sys.stdin)
login_employee(p['directory'],Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt'),
 p['username'],p['password'])
"""
        self.ssh('client', 'sudo /opt/vanguard/venv/bin/python -c ' + shlex.quote(code),
                 json.dumps({**credentials, 'directory': directory}).encode())
        return path

    def install(self, archive):
        for role in ROLES:
            print(f"Installing {role}…", flush=True)
            self.ssh(
                role,
                "mkdir -p ~/vanguard-release && tar xzf - -C ~/vanguard-release",
                archive.read_bytes(),
            )
            output = self.ssh(
                role,
                f"sudo env DEBIAN_FRONTEND=noninteractive bash ~/vanguard-release/deploy/install.sh {role}",
            )
            (self.state / f"install-{role}.log").write_bytes(output)
            print(f"Installed {role}", flush=True)

    def configure(self):
        self.ssh(
            "ca",
            "sudo test -f /var/lib/vanguard/ca/root.crt || sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init",
        )
        root = self.ssh("ca", "sudo cat /var/lib/vanguard/ca/root.crt")
        (self.state / "root.crt").write_bytes(root)
        for role in ROLES:
            self.write(role, "/etc/vanguard/root.crt", root, 0o644)
        for role in ("ca", "server", "admin"):
            print(f"Configuring TLS for {role}…", flush=True)
            self.ssh(
                role,
                "sudo test -f /etc/vanguard/tls.key || sudo openssl req -new -newkey rsa:3072 -nodes -keyout /etc/vanguard/tls.key -out /etc/vanguard/tls.csr -subj /CN=VanGuard-Service",
            )
            self.ssh(
                role,
                "sudo chown root:vanguard /etc/vanguard/tls.key && sudo chmod 0640 /etc/vanguard/tls.key",
            )
            csr = self.ssh(role, "sudo cat /etc/vanguard/tls.csr")
            prefix = (
                "/var/lib/vanguard/ca/requests/" + role + "-" + hashlib.sha256(csr).hexdigest()[:16]
            )
            self.ssh(
                "ca",
                "sudo install -d -m 0700 -o vanguard -g vanguard /var/lib/vanguard/ca/requests",
            )
            self.write("ca", prefix + ".csr", csr, owner="vanguard")
            ip = {"ca": "192.168.100.10", "server": "192.168.100.20", "admin": "192.168.100.40"}[
                role
            ]
            self.ssh(
                "ca",
                f"sudo test -f {prefix}.crt || sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca sign-tls --csr {prefix}.csr --ip {ip} --out {prefix}.crt",
            )
            certificate = self.ssh("ca", f"sudo cat {prefix}.crt")
            self.write(role, "/etc/vanguard/tls.crt", certificate, 0o644)
            self.ssh(role, "openssl verify -CAfile /etc/vanguard/root.crt /etc/vanguard/tls.crt")
        configs = {}
        for role in ("ca", "server", "admin"):
            current = self.ssh(role, f"sudo cat /etc/vanguard/{role}.env").decode()
            configs[role] = dict(
                line.split("=", 1)
                for line in current.splitlines()
                if "=" in line and not line.startswith("#")
            )
        ca_token = configs["ca"].get("VANGUARD_CA_TOKEN") or secrets.token_hex(32)
        server_token = configs["server"].get("VANGUARD_SERVER_TOKEN") or secrets.token_hex(32)
        configs["ca"]["VANGUARD_CA_TOKEN"] = ca_token
        configs["server"]["VANGUARD_SERVER_TOKEN"] = server_token
        configs["admin"].update(
            VANGUARD_CA_TOKEN=ca_token,
            VANGUARD_SERVER_TOKEN=server_token,
            VANGUARD_SESSION_SECRET=configs["admin"].get("VANGUARD_SESSION_SECRET")
            or secrets.token_hex(32),
        )
        for role, config in configs.items():
            self.write(
                role,
                f"/etc/vanguard/{role}.env",
                "".join(f"{key}={value}\n" for key, value in config.items()).encode(),
            )
        self.ssh(
            "client",
            "sudo test -f /var/lib/vanguard/client/identity.key || sudo /opt/vanguard/venv/bin/vanguard-client init --device-id vm-client",
        )
        server_key = self.ssh("server", "sudo cat /etc/vanguard/server-wg.pub")
        (self.state / "server-wg.pub").write_bytes(server_key)
        self.write(
            "client", "/etc/vanguard/client.env", b"VANGUARD_SERVER_WG_PUBLIC_KEY=" + server_key
        )
        print("CA, TLS, service tokens and client identity configured.", flush=True)

    def admin(self):
        import pyotp

        credentials_path = self.state / "admin-onboarding.json"
        if credentials_path.exists():
            print("Administrator onboarding file already exists; preserving account.")
            return
        credentials = {
            "username": "admin",
            "password": secrets.token_urlsafe(24),
            "totp_secret": pyotp.random_base32(),
        }
        code = """import json,sys
from vanguard.admin import Dashboard
from vanguard.common import database
from werkzeug.security import generate_password_hash
c=json.load(sys.stdin)
d=Dashboard('/var/lib/vanguard/admin',None,None)
with database(d.db) as db:
 db.execute('INSERT INTO users(username,password_hash,totp_secret) VALUES (?,?,?)',(c['username'],generate_password_hash(c['password']),c['totp_secret']))
"""
        self.ssh(
            "admin",
            "sudo -u vanguard /opt/vanguard/venv/bin/python -c " + shlex.quote(code),
            json.dumps(credentials).encode(),
        )
        credentials["totp_uri"] = pyotp.TOTP(credentials["totp_secret"]).provisioning_uri(
            "admin", issuer_name="VanGuard"
        )
        fd = os.open(credentials_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as output:
            json.dump(credentials, output, indent=2)
        print(f"Administrator created; private onboarding file: {credentials_path}", flush=True)

    def start(self):
        self.ssh("ca", "sudo systemctl enable --now vanguard-ca")
        self.ssh(
            "server",
            "sudo systemctl enable wg-quick@wg0 vanguard-daemon vanguard-server && sudo systemctl start vanguard-server",
        )
        self.ssh("admin", "sudo systemctl enable --now vanguard-admin")
        for role in ("ca", "server", "admin"):
            print(
                role, self.ssh(role, f"sudo systemctl is-active vanguard-{role}").decode().strip()
            )

    def enroll(self):
        before = self.ssh("server", "sudo wg show wg0 peers")
        (self.state / "peers-before-registration.txt").write_bytes(before)
        request = self.ssh("client", "sudo cat /var/lib/vanguard/client/request.json")
        code = """import json,os,sys
from vanguard.admin import Dashboard
from vanguard.common import Remote,Rejected,required_secret
body=json.load(sys.stdin)
trust=os.environ.get('VANGUARD_ROOT_CERT','/etc/vanguard/root.crt')
d=Dashboard('/var/lib/vanguard/admin',Remote(os.environ['VANGUARD_CA_URL'],trust,required_secret('VANGUARD_CA_TOKEN')),Remote(os.environ['VANGUARD_SERVER_URL'],trust,required_secret('VANGUARD_SERVER_TOKEN')))
try:
 d.register(body)
except Rejected:
 row=d.device(body['device_id'])
 if row['status'] != 'registered': d.retry(body['device_id'])
sys.stdout.write(d.device(body['device_id'])['certificate'])
"""
        inner = (
            "set -a; . /etc/vanguard/admin.env; set +a; exec sudo -E -u vanguard "
            "/opt/vanguard/venv/bin/python -c " + shlex.quote(code)
        )
        certificate = self.ssh("admin", "sudo bash -c " + shlex.quote(inner), request)
        self.write("client", "/var/lib/vanguard/client/device.crt", certificate)
        after = self.ssh("server", "sudo wg show wg0 peers")
        (self.state / "peers-after-registration.txt").write_bytes(after)
        if before != after:
            raise RuntimeError("Peer state changed during registration; inspect before connecting")
        self.employee_access()
        self.ssh("client", "sudo systemctl enable --now vanguard-client")
        self.ssh(
            "client",
            "for i in $(seq 1 30); do systemctl is-active --quiet vanguard-client && "
            "ping -c 1 -W 1 10.8.0.1 >/dev/null && exit 0; sleep 2; done; "
            "sudo systemctl status --no-pager vanguard-client; exit 1",
            timeout=90,
        )
        # Human-readable output hides private/preshared keys; `dump` exposes them.
        peers = self.ssh("server", "sudo wg show wg0")
        (self.state / "wireguard-after-enrollment.txt").write_bytes(peers)
        print("Client admitted; WireGuard handshake and ping to 10.8.0.1 succeeded.", flush=True)

    def negative_tests(self):
        output = self.ssh(
            "attacker", "/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py"
        )
        (self.state / "attacker-checks.txt").write_bytes(output)
        print(output.decode().strip(), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    parser.add_argument("--archive", type=Path, default=Path("dist/vanguard-0.1.0.tar.gz"))
    parser.add_argument(
        "--phase",
        choices=("install", "configure", "admin", "start", "enroll", "negative_tests", "all"),
        default="all",
    )
    args = parser.parse_args()
    os.umask(0o077)
    inventory = json.loads(args.inventory.read_text())
    if set(inventory) != set(ROLES):
        parser.error("Five-node inventory required")
    for item in inventory.items():
        result = check(item)
        if not result["ok"]:
            raise RuntimeError(f"SSH preflight failed: {result}")
    deployment = Deployment(inventory, args.state)
    for phase in ("install", "configure", "admin", "start", "enroll", "negative_tests"):
        if args.phase in (phase, "all"):
            if phase == "install":
                deployment.install(args.archive)
            else:
                getattr(deployment, phase)()


if __name__ == "__main__":
    main()
