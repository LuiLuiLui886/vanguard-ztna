#!/usr/bin/env python3
"""Run repeatable S-03 capture or S-04 revocation beside the main client."""

import argparse
import hashlib
import json
import math
import os
import secrets
import shlex
import signal
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from evidence import save_json
from verify_lab import Verification


def summarize_bounds(rounds):
    values = [r['confirmed_block_upper_seconds'] for r in rounds]
    if not values or any(r.get('status') != 'PASS' or not math.isfinite(v) or v < 0 or v >= 60
                         for r, v in zip(rounds, values)):
        raise ValueError('Only completed passing observations may be summarized')
    return {'n': len(values), 'mean_upper_seconds': statistics.mean(values),
            'median_upper_seconds': statistics.median(values),
            'min_upper_seconds': min(values), 'max_upper_seconds': max(values),
            'metric': 'conservative observation bound including SSH, polling and confirmation',
            'MTTD': None, 'MTTR': None}


class Experiment(Verification):
    def __init__(self, inventory, state, phase, rounds):
        super().__init__(inventory, state)
        self.output = state / 'security-results.json'
        if self.output.exists():
            raise ValueError('Evidence already exists; choose a new state directory')
        self.phase, self.rounds = phase, rounds
        self.remote = '/var/lib/vanguard/security-' + uuid.uuid4().hex[:12]
        self.report = {'status': 'RUNNING', 'phase': phase, 'requested_rounds': rounds,
                       'utc': datetime.now(timezone.utc).isoformat(), 'rounds': [],
                       'remote_tools': self.remote}
        self.save()

    def save(self):
        save_json(self.output, self.report)

    def worker(self, role, action, params):
        return json.loads(self.ssh(role, 'sudo /opt/vanguard/venv/bin/python '
                                  + shlex.quote(self.remote + '/worker.py') + ' ' + action,
                                  json.dumps(params).encode(), timeout=45))

    def stage(self, result, name):
        result['current_step'] = name
        self.save()

    def watchdog(self, role, params):
        config = self.remote + '/' + params['comment'] + '.json'
        self.write(role, config, json.dumps(params).encode())
        unit = params['comment'] + '-' + role
        self.ssh(role, 'sudo systemd-run --unit=' + unit
                 + ' --on-active=180s --timer-property=AccuracySec=1s '
                 '/opt/vanguard/venv/bin/python ' + shlex.quote(self.remote + '/worker.py')
                 + ' cleanup-' + role + ' ' + shlex.quote(config))
        return unit

    def capture_round(self, result):
        directory = self.remote + '/capture-' + str(result['number'])
        result['directory'] = directory
        self.stage(result, 'capture')
        result.update(self.worker('client', 'capture', {
            'directory': directory, 'marker': secrets.token_hex(16)}))
        self.stage(result, 'preserve_capture')
        for name in ('underlay', 'plaintext_control'):
            for suffix in ('.pcap', '.log'):
                data = self.ssh('client', 'sudo cat ' + shlex.quote(directory + '/' + name + suffix))
                (self.state / (str(result['number']) + '-' + name + suffix)).write_bytes(data)

    def peer_state(self, name, public):
        return json.loads(self.python('server', """import json,sqlite3,sys,subprocess
p=json.load(sys.stdin)
c=sqlite3.connect('file:/var/lib/vanguard/server/server.db?mode=ro',uri=True)
c.row_factory=sqlite3.Row
event=c.execute("SELECT timestamp,detail FROM audit WHERE device_id=? AND event='peer_removed' ORDER BY id DESC LIMIT 1",(p['name'],)).fetchone()
print(json.dumps({'present':p['public'] in subprocess.check_output(['wg','show','wg0','peers'],text=True).split(),
 'removal':dict(event) if event else None}))
""", json.dumps({'name': name, 'public': public}).encode()))

    def revocation_round(self, result):
        tag = 'vgs' + uuid.uuid4().hex[:8]
        name = 's04-' + uuid.uuid4().hex[:12]
        directory = '/var/lib/vanguard/' + name
        params = {'namespace': tag, 'interface': tag, 'comment': tag,
                  'directory': directory,
                  'server_key': self.ssh('server', 'sudo cat /etc/vanguard/server-wg.pub').decode().strip()}
        result.update(device_id=name, directory=directory, resources=params)
        registered, units, errors = False, {}, []
        before_firewall = self.ssh('server', 'sudo nft -s list ruleset')
        (self.state / (name + '-firewall-before.nft')).write_bytes(before_firewall)
        result['firewall_before_sha256'] = hashlib.sha256(before_firewall).hexdigest()
        try:
            self.stage(result, 'registration')
            self.ssh('client', 'sudo /opt/vanguard/venv/bin/vanguard-client --directory '
                     + directory + ' init --device-id ' + name)
            request = json.loads(self.ssh('client', 'sudo cat ' + directory + '/request.json'))
            request['tunnel_ip'] = '10.8.0.3'
            certificate = self.register_identity(request, directory)
            registered = True
            self.write('client', directory + '/device.crt', certificate)
            if self.peer_state(name, request['wg_public_key'])['present']:
                raise RuntimeError('Registration unexpectedly added peer')
            self.stage(result, 'watchdogs')
            for role in ('client', 'server'):
                units[role] = self.watchdog(role, params)
            result['watchdogs'] = units
            self.stage(result, 'temporary_icmp_rule')
            result['test_rule'] = self.worker('server', 'allow', params)
            self.stage(result, 'admitted_namespace')
            result['admission'] = self.worker('client', 'configure', params)
            self.stage(result, 'positive_traffic')
            # Warm up the actual handshake, then require five consecutive successes.
            deadline = time.monotonic() + 10
            while not self.worker('client', 'probe', params)['received']:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Test tunnel did not establish')
            result['before_revoke'] = [self.worker('client', 'probe', params) for _ in range(5)]
            if not all(p['received'] == 1 for p in result['before_revoke']):
                raise RuntimeError('Unstable positive traffic')
            self.ssh('client', 'ping -c 2 -W 1 10.8.0.1 >/dev/null')
            self.stage(result, 'ca_only_revoke')
            started = time.monotonic()
            result['request_host_utc'] = datetime.now(timezone.utc).isoformat()
            self.save()
            self.dashboard("row=d.device(" + repr(name) + ")\n"
                           "d.ca.call('POST','/api/ca/revoke',{'serial':row['serial']})\n")
            result['revoke_call_upper_seconds'] = time.monotonic() - started
            self.stage(result, 'observe_block')
            result['probes'] = []
            while time.monotonic() - started < 45:
                probe = self.worker('client', 'probe', params)
                state = self.peer_state(name, request['wg_public_key'])
                result['probes'].append({**probe, 'peer_present': state['present'],
                                         'end_offset_seconds': time.monotonic() - started})
                self.save()
                if probe['received'] == 0 and not state['present']:
                    removal = state['removal']
                    if not removal or json.loads(removal['detail'])['reason'] != 'certificate_revoked':
                        raise RuntimeError('Missing certificate_revoked evidence')
                    result['removal_audit'] = removal
                    result['first_block_upper_seconds'] = time.monotonic() - started
                    break
            else:
                raise RuntimeError('No confirmed peer/traffic block within observation budget')
            self.stage(result, 'confirm_no_replies')
            result['confirmation'] = self.worker('client', 'probe', {**params, 'confirm': True})
            result['confirmed_block_upper_seconds'] = time.monotonic() - started
            if result['confirmation']['received'] or result['confirmed_block_upper_seconds'] >= 60:
                raise RuntimeError('Traffic continued or confirmed bound exceeded 60 seconds')
            self.python('client', """import sys
from vanguard.client import admit
from vanguard.common import Remote,Rejected
try:
 admit(sys.stdin.read(),Remote('https://192.168.100.20:8081','/etc/vanguard/root.crt'))
except Rejected as e:
 assert getattr(e,'upstream_status',None)==403
else: raise RuntimeError('Revoked identity readmitted')
""", directory.encode())
            result['readmission'] = 'denied_403'
        finally:
            if sys.exc_info()[0] is not None:
                result['failed_step'] = result.get('current_step')
            self.stage(result, 'cleanup')
            for role in ('client', 'server'):
                if role in units:
                    try:
                        self.worker(role, 'cleanup-' + role, params)
                        self.ssh(role, 'sudo systemctl stop ' + units[role] + '.timer')
                    except Exception as exc:
                        errors.append(role + ': ' + str(exc))
            if registered:
                try:
                    self.cleanup_identity(name)
                except Exception as exc:
                    errors.append('identity: ' + str(exc))
            try:
                after_firewall = self.ssh('server', 'sudo nft -s list ruleset')
                result['firewall_after_sha256'] = hashlib.sha256(after_firewall).hexdigest()
                if after_firewall != before_firewall:
                    raise RuntimeError('Firewall did not return to original rules')
                self.ssh('client', 'ping -c 2 -W 1 10.8.0.1 >/dev/null')
            except Exception as exc:
                errors.append('restoration: ' + str(exc))
            result['cleanup'] = {'status': 'FAIL' if errors else 'PASS', 'errors': errors}
            self.save()
            if errors:
                raise RuntimeError('Cleanup incomplete; inspect recorded resources')

    def run(self):
        try:
            for role in ('client', 'server') if self.phase == 'revocation' else ('client',):
                self.write(role, self.remote + '/worker.py', Path('scripts/security_worker.py').read_bytes())
            for number in range(1, self.rounds + 1):
                result = {'number': number, 'status': 'RUNNING'}
                self.report['rounds'].append(result)
                self.save()
                if self.phase == 'capture':
                    self.capture_round(result)
                else:
                    self.revocation_round(result)
                result.update(status='PASS', current_step=None)
                self.save()
                print(f'PASS {self.phase} {number}/{self.rounds}', flush=True)
            if self.phase == 'revocation':
                self.report['summary'] = summarize_bounds(self.report['rounds'])
            self.report['status'] = 'COMPLETE'
        except BaseException as exc:
            self.report['status'] = 'INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAIL'
            self.report['error'] = str(exc)
            if self.report['rounds'] and self.report['rounds'][-1]['status'] == 'RUNNING':
                self.report['rounds'][-1]['status'] = self.report['status']
            raise
        finally:
            self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('phase', choices=('capture', 'revocation'))
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 10:
        parser.error('rounds must be between 1 and 10')
    os.umask(0o077)
    def interrupt(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    Experiment(json.loads(args.inventory.read_text()), args.state, args.phase, args.rounds).run()


if __name__ == '__main__':
    main()
