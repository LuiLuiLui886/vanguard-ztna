"""Explicit lab resource grants, enforced before conntrack established accepts."""

import json
import math
import time
from pathlib import Path

from .common import Rejected, database, device_name, run, tunnel_ip

RESOURCE = {'resource': 'internal-demo', 'address': '10.8.0.1', 'protocol': 'tcp', 'port': 8082}


def load_policy(path):
    try:
        value = json.loads(Path(path).read_text())
        if set(value) != {'grants'} or not isinstance(value['grants'], list):
            raise ValueError()
        grants = set()
        for item in value['grants']:
            if set(item) != set(RESOURCE) | {'device_id', 'username'}:
                raise ValueError()
            if any(item[key] != expected for key, expected in RESOURCE.items()):
                raise ValueError()
            grants.add((device_name(item['device_id']), device_name(item['username'])))
        return grants
    except (OSError, ValueError, TypeError) as exc:
        raise Rejected('Resource policy invalid or unavailable', 503) from exc


class NftResources:
    def __init__(self, policy):
        self.policy = Path(policy)

    def clear(self):
        run(['nft', '-f', '-'], input=b'flush set inet vanguard application_access\n', timeout=2)

    def sync(self, db_path, peers):
        # Atomic nft batch keeps other sessions' grants while removing revoked
        # access. Timeout never extends the recorded admission lease.
        command = 'flush set inet vanguard application_access\n'
        try:
            grants = load_policy(self.policy)
            with database(db_path) as db:
                rows = db.execute('SELECT d.*,e.username,s.expires FROM devices d '
                                  'JOIN employee_devices e ON e.device_id=d.device_id '
                                  'JOIN employees u ON u.username=e.username '
                                  'JOIN employee_leases l ON l.device_id=d.device_id '
                                  'JOIN employee_sessions s ON s.token_hash=l.token_hash '
                                  'AND s.username=e.username '
                                  'WHERE d.enabled=1 AND u.enabled=1').fetchall()
            for row in rows:
                remaining = math.floor(min(row['lease_until'], row['expires']) - time.time()) - 2
                if (remaining > 0 and row['wg_public_key'] in peers
                        and (row['device_id'], row['username']) in grants):
                    ip = tunnel_ip(row['tunnel_ip'])
                    command += ('add element inet vanguard application_access { '
                                f'{ip} . 10.8.0.1 . tcp . 8082 timeout {remaining}s }}\n')
        except Exception:
            run(['nft', '-f', '-'], input=command.splitlines()[0].encode() + b'\n', timeout=2)
            raise
        run(['nft', '-f', '-'], input=command.encode(), timeout=2)
