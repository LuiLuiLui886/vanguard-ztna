"""Opt-in IPv4 Internet grants. Routes alone never authorize forwarding."""

import json
import math
import time
from pathlib import Path

from .common import Rejected, database, device_name, run, tunnel_ip


def load_internet_policy(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict) or set(value) != {'grants'} or not isinstance(value['grants'], list):
        raise ValueError('Invalid Internet policy')
    grants = set()
    for item in value['grants']:
        if not isinstance(item, dict) or set(item) != {'device_id', 'username', 'resource'} or item['resource'] != 'internet-ipv4':
            raise ValueError('Invalid Internet grant')
        grants.add((device_name(item['device_id']), device_name(item['username'])))
    return grants


class NftInternet:
    def __init__(self, policy):
        self.policy = Path(policy)

    def clear(self):
        run(['nft', '-f', '-'], input=b'flush set inet vanguard internet_access\n', timeout=2)

    def sync(self, db_path, peers):
        command = 'flush set inet vanguard internet_access\n'
        try:
            grants = load_internet_policy(self.policy)
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
                    command += ('add element inet vanguard internet_access { '
                                f"{tunnel_ip(row['tunnel_ip'])} timeout {remaining}s }}\n")
        except Exception as exc:
            self.clear()
            raise Rejected('Internet policy invalid or unavailable; forwarding denied', 503) from exc
        run(['nft', '-f', '-'], input=command.encode(), timeout=2)


class AccessPolicies:
    """If any policy fails, clear every grant class before propagating the error."""
    def __init__(self, policies):
        self.policies = policies

    def sync(self, db_path, peers):
        try:
            for policy in self.policies:
                policy.sync(db_path, peers)
        except Exception:
            for policy in self.policies:
                try:
                    policy.clear()
                except Exception:
                    pass  # Original failure propagates; admission removes its peer.
            raise
