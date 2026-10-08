#!/usr/bin/env bash
# Start the existing lab and open its dashboard; never provision or replace a VM.
set -euo pipefail
for vm in VM-CA VM-SERVER VM-CLIENT VM-ADMIN VM-ATTACKER; do
    state=$(LC_ALL=C virsh -c qemu:///system domstate "$vm")
    case "$state" in
        running) ;;
        'shut off') virsh -c qemu:///system start "$vm" ;;
        *) echo "$vm is $state; inspect it in Virtual Machine Manager." >&2; exit 1 ;;
    esac
done
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for attempt in {1..90}; do
    if curl --silent --fail --max-time 2 --cacert "$project_dir/state/deployment/root.crt" \
        https://192.168.100.40:5000/healthz >/dev/null; then
        exec xdg-open https://192.168.100.40:5000
    fi
    sleep 2
done
echo 'Dashboard has not become ready; inspect VM-ADMIN in Virtual Machine Manager.' >&2
exit 1
