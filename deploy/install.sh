#!/usr/bin/env bash
# Run on the intended VM as root; installs files but never starts services or changes firewall.
set -euo pipefail
umask 077
role=${1:-}
case "$role" in ca|server|client|admin|attacker) ;; *) echo "Usage: sudo bash deploy/install.sh ca|server|client|admin|attacker" >&2; exit 2;; esac
[[ $EUID -eq 0 ]] || { echo 'Run as root on the target VM.' >&2; exit 1; }
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
. /etc/os-release
[[ "$ID" = ubuntu && "$VERSION_ID" = 22.04 ]] || { echo 'This installer targets Ubuntu Server 22.04.' >&2; exit 1; }
case "$role" in ca) expected_ip=192.168.100.10;; server) expected_ip=192.168.100.20;; client) expected_ip=192.168.100.30;; admin) expected_ip=192.168.100.40;; attacker) expected_ip=192.168.100.50;; esac
ip -4 -o address show | awk '{print $4}' | cut -d/ -f1 | grep -Fxq "$expected_ip" || { echo "Expected local address $expected_ip; refusing wrong-node installation." >&2; exit 1; }
apt-get update
apt-get install -y python3-venv python3-pip openssl ca-certificates
if [[ "$role" = server || "$role" = client || "$role" = attacker ]]; then apt-get install -y wireguard-tools iproute2 iputils-ping; fi
id vanguard >/dev/null 2>&1 || useradd --system --home-dir /var/lib/vanguard --create-home --shell /usr/sbin/nologin vanguard
install -d -m 0755 /opt/vanguard /etc/vanguard /var/lib/vanguard
install -d -m 0700 -o vanguard -g vanguard "/var/lib/vanguard/$role"
python3 -m venv /opt/vanguard/venv
/opt/vanguard/venv/bin/pip install -c "$source_dir/deploy/constraints.txt" "$source_dir"
# The venv contains application code only; service users need traverse/read/execute access.
# Secrets and mutable state remain under /etc/vanguard and /var/lib/vanguard.
chmod -R a+rX /opt/vanguard/venv
if [[ "$role" = ca || "$role" = server || "$role" = admin ]]; then
    install -m 0644 "$source_dir/deploy/systemd/vanguard-$role.service" /etc/systemd/system/
    if [[ ! -e "/etc/vanguard/$role.env" ]]; then install -m 0600 "$source_dir/deploy/env/$role.env.example" "/etc/vanguard/$role.env"; fi
fi
if [[ "$role" = server ]]; then
    chown root:root /var/lib/vanguard/server
    install -m 0644 "$source_dir/deploy/systemd/vanguard-daemon.service" /etc/systemd/system/
    install -d -m 0700 /etc/wireguard
    if [[ ! -e /etc/wireguard/wg0.conf ]]; then
        server_private=$(wg genkey)
        { printf '[Interface]\nAddress = 10.8.0.1/24\nListenPort = 51820\nPrivateKey = %s\n' "$server_private"; } > /etc/wireguard/wg0.conf
        printf '%s' "$server_private" | wg pubkey > /etc/vanguard/server-wg.pub
        unset server_private
    fi
fi
if [[ "$role" = attacker ]]; then
    install -m 0755 "$source_dir/scripts/attacker_checks.py" /opt/vanguard/attacker_checks.py
fi
if [[ "$role" = client ]]; then
    install -m 0644 "$source_dir/deploy/systemd/vanguard-client.service" /etc/systemd/system/
fi
systemctl daemon-reload
echo "Installed $role. Complete TLS, tokens, ownership and firewall using docs/DEPLOYMENT.md before starting."
