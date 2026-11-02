"""Admission API and periodic, fail-closed WireGuard reconciliation."""

import argparse
import json
import os
import secrets
import socket
import sqlite3
import time
from pathlib import Path

from .ca_storage import durable_write
from .common import (
    Rejected,
    Remote,
    bearer,
    database,
    device_name,
    json_body,
    locked,
    make_app,
    private_dir,
    required_secret,
    run,
    tunnel_ip,
    wg_key,
)
from .employees import Employees
from .operations import storage_summary
from .pki import (
    fingerprint,
    load_cert,
    proof_message,
    validate_certificate,
    validate_fetched_crl,
    verify_proof,
)
from .resource_policy import NftResources
from .telemetry import install_denial_timing


class WireGuard:
    def __init__(self, interface="wg0"):
        if interface != "wg0":
            raise RuntimeError("VanGuard lab requires wg0")
        self.interface = interface

    def peers(self):
        return set(run(["wg", "show", self.interface, "peers"]).stdout.decode().split())

    def observations(self):
        # Never use `wg show dump`: its interface row contains the private key.
        peers = set(run(['wg', 'show', self.interface, 'peers'], timeout=1).stdout.decode().split())
        result = {key: {'last_handshake': None, 'rx_bytes': None, 'tx_bytes': None} for key in peers}
        handshakes = run(['wg', 'show', self.interface, 'latest-handshakes'], timeout=1)
        transfer = run(['wg', 'show', self.interface, 'transfer'], timeout=1)
        for line in handshakes.stdout.decode().splitlines():
            key, timestamp = line.split()
            if key in result:
                result[key]['last_handshake'] = int(timestamp)
        for line in transfer.stdout.decode().splitlines():
            key, received, sent = line.split()
            if key in result:
                result[key].update(rx_bytes=int(received), tx_bytes=int(sent))
        return result

    def add(self, public_key, ip):
        run(
            [
                "wg",
                "set",
                self.interface,
                "peer",
                wg_key(public_key),
                "allowed-ips",
                tunnel_ip(ip) + "/32",
            ]
        )

    def remove(self, public_key):
        run(["wg", "set", self.interface, "peer", wg_key(public_key), "remove"])


class Admission:
    def __init__(self, directory, root_pem, fetch_crl, wireguard, lease_seconds=300, resources=None):
        self.path = private_dir(directory)
        self.db = self.path / "server.db"
        self.lock = self.path / "admission.lock"
        self.root = load_cert(root_pem)
        self.fetch_crl = fetch_crl
        self.wg = wireguard
        self.lease_seconds = lease_seconds
        self.resources = resources
        with database(self.db) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY, serial TEXT UNIQUE NOT NULL,
                    fingerprint TEXT UNIQUE NOT NULL, certificate TEXT NOT NULL,
                    wg_public_key TEXT UNIQUE NOT NULL, tunnel_ip TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1, lease_until REAL NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY, device_id TEXT NOT NULL, nonce TEXT NOT NULL,
                    expires REAL NOT NULL, FOREIGN KEY(device_id) REFERENCES devices(device_id)
                );
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, timestamp REAL NOT NULL, event TEXT NOT NULL,
                    device_id TEXT, detail TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rate_limits (
                    bucket TEXT PRIMARY KEY, start REAL NOT NULL, count INTEGER NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS active_tunnel_ip ON devices(tunnel_ip) WHERE enabled=1;
            """)
        self.employees = Employees(self.db)

    def audit(self, event, name, detail):
        with database(self.db) as db:
            db.execute(
                "INSERT INTO audit(timestamp,event,device_id,detail) VALUES (?,?,?,?)",
                (time.time(), event, name, detail),
            )

    def throttle(self, source):
        at = time.time()
        with database(self.db) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM rate_limits WHERE start < ?", (at - 60,))
            for bucket, maximum in (("global", 240), ("ip:" + source, 30)):
                db.execute(
                    "INSERT INTO rate_limits VALUES (?,?,1) ON CONFLICT(bucket) "
                    "DO UPDATE SET count=count+1",
                    (bucket, at),
                )
                if (
                    db.execute(
                        "SELECT count FROM rate_limits WHERE bucket=?", (bucket,)
                    ).fetchone()[0]
                    > maximum
                ):
                    raise Rejected("Admission rate limit reached", 429)

    def current_crl(self):
        return validate_fetched_crl(self.root, self.fetch_crl())

    def register(self, body):
        name, key, ip = (
            device_name(body["device_id"]),
            wg_key(body["wg_public_key"]),
            tunnel_ip(body["tunnel_ip"]),
        )
        with locked(self.lock):
            cert = validate_certificate(self.root, body["certificate"], self.current_crl(), name)
            try:
                with database(self.db) as db:
                    existing = db.execute(
                        "SELECT * FROM devices WHERE device_id=?", (name,)
                    ).fetchone()
                    if existing:
                        if (
                            existing["enabled"]
                            and existing["fingerprint"] == fingerprint(cert)
                            and existing["wg_public_key"] == key
                            and existing["tunnel_ip"] == ip
                        ):
                            return {"device_id": name, "registered": True}
                        raise Rejected(
                            "Device identity already exists; identities are immutable", 409
                        )
                    db.execute(
                        "INSERT INTO devices(device_id,serial,fingerprint,certificate,wg_public_key,tunnel_ip) "
                        "VALUES (?,?,?,?,?,?)",
                        (
                            name,
                            format(cert.serial_number, "X"),
                            fingerprint(cert),
                            body["certificate"],
                            key,
                            ip,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise Rejected(
                    "Certificate, WireGuard key, or tunnel IP already registered", 409
                ) from exc
            self.audit("registered", name, "Registry only; no live peer added")
        return {"device_id": name, "registered": True}

    def challenge(self, body):
        cert = load_cert(body["certificate"])
        with locked(self.lock), database(self.db) as db:
            row = db.execute(
                "SELECT * FROM devices WHERE fingerprint=? AND enabled=1", (fingerprint(cert),)
            ).fetchone()
            if not row or row["wg_public_key"] != body["wg_public_key"]:
                raise Rejected("Device binding rejected", 403)
            session_hash, _ = self.employees.require(body.get("employee_session"), row["device_id"])
            # Check trust/revocation before allocating a challenge, and again on verification.
            validate_certificate(
                self.root, body["certificate"], self.current_crl(), row["device_id"]
            )
            db.execute("DELETE FROM challenges WHERE expires <= ?", (time.time(),))
            db.execute("DELETE FROM employee_challenges WHERE challenge_id NOT IN "
                       "(SELECT id FROM challenges)")
            if (
                db.execute(
                    "SELECT count(*) FROM challenges WHERE device_id=?", (row["device_id"],)
                ).fetchone()[0]
                >= 5
            ):
                raise Rejected("Too many outstanding challenges", 429)
            identity, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            expires = time.time() + 60
            db.execute(
                "INSERT INTO challenges VALUES (?,?,?,?)",
                (identity, row["device_id"], nonce, expires),
            )
            db.execute("INSERT INTO employee_challenges VALUES (?,?)", (identity, session_hash))
            message = proof_message(
                identity, nonce, row["fingerprint"], row["wg_public_key"], row["tunnel_ip"]
            )
            return {
                "challenge_id": identity,
                "nonce": nonce,
                "expires_at": expires,
                "tunnel_ip": row["tunnel_ip"],
                "message": message.decode(),
            }

    def verify(self, body):
        name = None
        try:
            with locked(self.lock):
                # Commit challenge consumption BEFORE validation so failures cannot replay it.
                with database(self.db) as db:
                    challenge = db.execute(
                        "SELECT * FROM challenges WHERE id=?", (body["challenge_id"],)
                    ).fetchone()
                    db.execute("DELETE FROM challenges WHERE id=?", (body["challenge_id"],))
                    employee_challenge = db.execute(
                        "SELECT token_hash FROM employee_challenges WHERE challenge_id=?",
                        (body["challenge_id"],),
                    ).fetchone()
                    db.execute("DELETE FROM employee_challenges WHERE challenge_id=?",
                               (body["challenge_id"],))
                    if challenge:
                        name = challenge["device_id"]
                        row = db.execute(
                            "SELECT * FROM devices WHERE device_id=?", (name,)
                        ).fetchone()
                if not challenge or challenge["expires"] <= time.time():
                    raise Rejected("Unknown, consumed, or expired challenge", 403)
                if not row or not row["enabled"]:
                    raise Rejected("Device disabled", 403)
                session_hash, employee = self.employees.require(body.get("employee_session"), name)
                if not employee_challenge or employee_challenge[0] != session_hash:
                    raise Rejected("Employee session does not match challenge", 403)
                crl = self.current_crl()
                cert = validate_certificate(self.root, body["certificate"], crl, name)
                if (
                    fingerprint(cert) != row["fingerprint"]
                    or body["wg_public_key"] != row["wg_public_key"]
                ):
                    raise Rejected("Device binding rejected", 403)
                message = proof_message(
                    body["challenge_id"],
                    challenge["nonce"],
                    row["fingerprint"],
                    row["wg_public_key"],
                    row["tunnel_ip"],
                )
                verify_proof(cert, body["signature"], message)
                lease = min(
                    time.time() + self.lease_seconds,
                    cert.not_valid_after_utc.timestamp(),
                    crl.next_update_utc.timestamp(),
                    self.root.not_valid_after_utc.timestamp(),
                    employee["expires"],
                )
                if lease <= time.time():
                    raise Rejected("Admission validity elapsed", 403)
                if challenge["expires"] <= time.time():
                    raise Rejected("Challenge expired during verification", 403)
                self.employees.require_hash(session_hash, name)
                try:
                    self.wg.add(row["wg_public_key"], row["tunnel_ip"])
                    with database(self.db) as db:
                        db.execute(
                            "UPDATE devices SET lease_until=? WHERE device_id=?", (lease, name)
                        )
                        db.execute("INSERT INTO employee_leases VALUES (?,?) "
                                   "ON CONFLICT(device_id) DO UPDATE SET token_hash=excluded.token_hash",
                                   (name, session_hash))
                    self.sync_resources()
                except Exception:
                    self.wg.remove(row["wg_public_key"])
                    raise
                self.audit("accepted", name, json.dumps({
                    "reason": "all_six_checks_and_employee_passed", "username": employee["username"]
                }, sort_keys=True))
                return {"decision": "ACCEPT", "tunnel_ip": row["tunnel_ip"], "lease_until": lease}
        except Rejected as exc:
            self.audit("rejected", name, str(exc))
            raise

    def disable(self, name):
        with locked(self.lock):
            with database(self.db) as db:
                row = db.execute("SELECT * FROM devices WHERE device_id=?", (name,)).fetchone()
                if not row:
                    raise Rejected("Unknown device", 404)
                db.execute("UPDATE devices SET enabled=0,lease_until=0 WHERE device_id=?", (name,))
                db.execute("DELETE FROM challenges WHERE device_id=?", (name,))
            self.wg.remove(row["wg_public_key"])
            self.sync_resources()
            self.audit("disabled", name, "Peer removed; identity cannot be re-enabled")
        return {"device_id": name, "disabled": True}

    def bind_employee(self, name, username):
        with locked(self.lock):
            result = self.employees.bind(name, username)
            self.audit("employee_bound", name, json.dumps({"username": username}))
            return result

    def disable_employee(self, username):
        with locked(self.lock):
            result = self.employees.disable(username)
            with database(self.db) as db:
                rows = db.execute("SELECT d.device_id,d.wg_public_key FROM devices d "
                                  "JOIN employee_devices e ON e.device_id=d.device_id "
                                  "WHERE e.username=?", (username,)).fetchall()
                for row in rows:
                    db.execute("UPDATE devices SET lease_until=0 WHERE device_id=?",
                               (row['device_id'],))
            for row in rows:
                self.wg.remove(row['wg_public_key'])
            self.sync_resources()
            self.audit("employee_disabled", None, json.dumps({"username": username}))
            return result

    def logout_employee(self, token):
        hashed = self.employees.token_hash(token)
        with locked(self.lock):
            with database(self.db) as db:
                known = db.execute('SELECT 1 FROM employee_sessions WHERE token_hash=?',
                                   (hashed,)).fetchone()
                retried = db.execute('SELECT 1 FROM employee_logouts WHERE token_hash=?',
                                     (hashed,)).fetchone()
                if not known and not retried:
                    raise Rejected('Employee session rejected', 403)
                db.execute('INSERT OR IGNORE INTO employee_logouts VALUES (?,?)',
                           (hashed, time.time()))
                db.execute('DELETE FROM employee_sessions WHERE token_hash=?', (hashed,))
                db.execute('DELETE FROM challenges WHERE id IN '
                           '(SELECT challenge_id FROM employee_challenges WHERE token_hash=?)',
                           (hashed,))
                db.execute('DELETE FROM employee_challenges WHERE token_hash=?', (hashed,))
                rows = db.execute('SELECT d.device_id,d.wg_public_key FROM devices d '
                                  'JOIN employee_leases l ON l.device_id=d.device_id '
                                  'WHERE l.token_hash=?', (hashed,)).fetchall()
                for row in rows:
                    db.execute('UPDATE devices SET lease_until=0 WHERE device_id=?',
                               (row['device_id'],))
            # Invalidity survives kernel failure. Keep lease ownership for retry;
            # a later lease under another token must not be removed by that retry.
            for row in rows:
                try:
                    self.wg.remove(row['wg_public_key'])
                except Rejected:
                    self.audit('employee_logout_pending', row['device_id'],
                               'Session revoked; peer removal unconfirmed')
                    raise Rejected('Session revoked; peer removal unconfirmed; retry logout', 503)
            with database(self.db) as db:
                db.execute('DELETE FROM employee_leases WHERE token_hash=?', (hashed,))
            self.sync_resources()
            if known or rows:
                self.audit('employee_logout', None, 'Session, challenges and scoped access revoked')
            return {'revoked': True, 'peer_removal_confirmed': True}

    def reconcile(self, startup=False):
        with locked(self.lock):
            allowed = set()
            reasons = {}
            crl_reason, crl_error = "crl_unavailable", None
            try:
                crl = self.current_crl() if not startup else None
            except Rejected as exc:
                crl = None
                crl_reason, crl_error = exc.reason or "crl_unavailable", str(exc)
            with database(self.db) as db:
                rows = db.execute("SELECT * FROM devices").fetchall()
                by_key = {row["wg_public_key"]: row for row in rows}
                for row in rows:
                    reason = None
                    if startup:
                        reason = "startup_reset"
                    elif crl is None:
                        reason = crl_reason
                    elif not row["enabled"]:
                        reason = "device_disabled"
                    else:
                        try:
                            session = db.execute("SELECT token_hash FROM employee_leases "
                                                 "WHERE device_id=?", (row['device_id'],)).fetchone()
                            self.employees.require_hash(session[0] if session else '', row['device_id'])
                            cert = validate_certificate(
                                self.root, row["certificate"], crl, row["device_id"]
                            )
                            if fingerprint(cert) != row["fingerprint"]:
                                reason = "binding_mismatch"
                            elif row["lease_until"] <= time.time():
                                reason = "lease_expired"
                        except Rejected as exc:
                            reason = exc.reason or "certificate_invalid"
                    if reason is None:
                        allowed.add(row["wg_public_key"])
                    else:
                        reasons[row["wg_public_key"]] = reason
                        db.execute(
                            "UPDATE devices SET lease_until=0 WHERE device_id=?",
                            (row["device_id"],),
                        )
                for key in self.wg.peers() - allowed:
                    self.wg.remove(key)
                    row = by_key.get(key)
                    detail = {
                        "reason": reasons.get(key, "unknown_peer"),
                        "wg_public_key": key,
                        "lease_until": row["lease_until"] if row else None,
                    }
                    if crl_error and row:
                        detail["crl_error"] = crl_error
                    db.execute(
                        "INSERT INTO audit(timestamp,event,device_id,detail) VALUES (?,?,?,?)",
                        (
                            time.time(),
                            "peer_removed",
                            row["device_id"] if row else None,
                            json.dumps(detail, sort_keys=True),
                        ),
                    )
            self.sync_resources()
            return {"eligible_peers": len(allowed), "crl_available": crl is not None}

    def sync_resources(self):
        if self.resources is not None:
            self.resources.sync(self.db, self.wg.peers())

    def internet_policy(self):
        from .internet import NftInternet
        for policy in getattr(self.resources, 'policies', [self.resources]):
            if isinstance(policy, NftInternet):
                return policy.policy
        return None

    def set_internet(self, name, enabled):
        from .internet import load_internet_policy
        if type(enabled) is not bool:
            raise Rejected('Internet permission must be an explicit boolean')
        path = self.internet_policy()
        if path is None:
            raise Rejected('Managed Internet gateway is not configured', 409)
        with locked(self.lock):
            with database(self.db) as db:
                row = db.execute('SELECT d.*,e.username FROM devices d '
                                 'JOIN employee_devices e ON e.device_id=d.device_id '
                                 'JOIN employees u ON u.username=e.username '
                                 'WHERE d.device_id=? AND d.enabled=1 AND u.enabled=1',
                                 (device_name(name),)).fetchone()
            if not row:
                raise Rejected('Device must be enabled and bound to an active employee', 409)
            try:
                grants = load_internet_policy(path)
            except (OSError, ValueError, TypeError) as exc:
                raise Rejected('Internet policy unavailable; existing evidence retained', 503) from exc
            grants.discard((name, row['username']))
            if enabled:
                grants.add((name, row['username']))
            durable_write(path, json.dumps({'grants': [
                {'device_id': device, 'username': user, 'resource': 'internet-ipv4'}
                for device, user in sorted(grants)]}).encode())
            try:
                self.sync_resources()
            except Exception:
                with database(self.db) as db:
                    db.execute('UPDATE devices SET lease_until=0 WHERE device_id=?', (name,))
                self.wg.remove(row['wg_public_key'])
                self.audit('internet_policy_failed', name, 'Enforcement unconfirmed; lease invalidated')
                raise
            self.audit('internet_granted' if enabled else 'internet_removed', name,
                       'Internet policy updated; admission and live lease still required')
        return {'device_id': name, 'internet_granted': enabled, 'admission_required': True}

    def listing(self):
        try:
            observed = (self.wg.observations() if hasattr(self.wg, 'observations')
                        else {key: {} for key in self.wg.peers()})
        except (Rejected, ValueError):
            observed = None
        internet_grants = None
        internet_path = self.internet_policy()
        if internet_path is not None:
            from .internet import load_internet_policy
            try:
                internet_grants = load_internet_policy(internet_path)
            except (OSError, ValueError, TypeError, Rejected):
                pass
        with database(self.db) as db:
            rows = db.execute(
                "SELECT device_id,serial,wg_public_key,tunnel_ip,enabled,lease_until FROM devices"
            ).fetchall()
            results = []
            for row in rows:
                peer = None if observed is None else row['wg_public_key'] in observed
                detail = (observed or {}).get(row['wg_public_key'], {})
                lease_valid = bool(row['enabled'] and row['lease_until'] > time.time())
                if lease_valid:
                    owner = db.execute('SELECT token_hash FROM employee_leases WHERE device_id=?',
                                       (row['device_id'],)).fetchone()
                    try:
                        self.employees.require_hash(owner[0] if owner else '', row['device_id'])
                    except Rejected:
                        lease_valid = False
                binding = db.execute('SELECT username FROM employee_devices WHERE device_id=?',
                                     (row['device_id'],)).fetchone()
                results.append(dict(row, registered=True,
                    internet_configured=internet_path is not None,
                    internet_granted=(bool(binding) and (row['device_id'], binding[0]) in internet_grants)
                    if internet_grants is not None else None,
                    lease_valid=lease_valid,
                    live=peer, peer_present=peer, last_handshake=detail.get('last_handshake'),
                    rx_bytes=detail.get('rx_bytes'), tx_bytes=detail.get('tx_bytes'),
                    observed_at=time.time() if observed is not None else None))
            return results


def from_environment():
    trust = os.environ.get("VANGUARD_ROOT_CERT", "/etc/vanguard/root.crt")
    ca = Remote(os.environ.get("VANGUARD_CA_URL", "https://192.168.100.10:8080"), trust)
    from .internet import AccessPolicies, NftInternet
    policies = []
    if os.environ.get('VANGUARD_RESOURCE_POLICY'):
        policies.append(NftResources(os.environ['VANGUARD_RESOURCE_POLICY']))
    if os.environ.get('VANGUARD_INTERNET_POLICY'):
        policies.append(NftInternet(os.environ['VANGUARD_INTERNET_POLICY']))
    return Admission(
        os.environ.get("VANGUARD_SERVER_DIR", "/var/lib/vanguard/server"),
        Path(trust).read_bytes(),
        lambda: ca.call("GET", "/api/ca/crl", raw=True),
        WireGuard(),
        resources=AccessPolicies(policies) if policies else None,
    )


def create_app(config=None):
    config = config or {}
    app = make_app(__name__)
    admission = config.get("ADMISSION") or from_environment()
    token = config.get("TOKEN") or required_secret("VANGUARD_SERVER_TOKEN")
    app.extensions["admission"] = admission
    install_denial_timing(app, admission.audit)
    if not config.get("TESTING"):
        admission.reconcile(startup=True)

    @app.post("/api/devices")
    @bearer(token)
    def register():
        return admission.register(
            json_body("device_id", "certificate", "wg_public_key", "tunnel_ip")
        ), 201

    @app.post('/api/devices/<name>/internet')
    @bearer(token)
    def internet_permission(name):
        return admission.set_internet(name, json_body().get('enabled'))

    @app.get("/api/devices")
    @bearer(token)
    def devices():
        return {"devices": admission.listing()}

    @app.get("/api/employees")
    @bearer(token)
    def employees():
        return {"employees": admission.employees.listing()}

    @app.post("/api/employees")
    @bearer(token)
    def create_employee():
        body = json_body("username", "password")
        with locked(admission.lock):
            result = admission.employees.create(body['username'], body['password'])
            admission.audit('employee_created', None, json.dumps({'username': body['username']}))
        return result, 201

    @app.post("/api/employees/<username>/disable")
    @bearer(token)
    def disable_employee(username):
        return admission.disable_employee(device_name(username))

    @app.post("/api/devices/<name>/employee")
    @bearer(token)
    def bind_employee(name):
        return admission.bind_employee(device_name(name), device_name(json_body('username')['username']))

    @app.post("/api/employee/login")
    def employee_login():
        admission.throttle(request_ip())
        body = json_body('username', 'password')
        try:
            with locked(admission.lock):
                result = admission.employees.login(body['username'], body['password'], request_ip())
            admission.audit('employee_login', None, json.dumps({'username': result['username']}))
            return result
        except Rejected:
            admission.audit('employee_login_rejected', None, 'Employee credentials rejected')
            raise

    @app.post('/api/employee/logout')
    def employee_logout():
        admission.throttle(request_ip())
        return admission.logout_employee(json_body('employee_session')['employee_session'])

    @app.post("/api/devices/<name>/disable")
    @bearer(token)
    def disable(name):
        return admission.disable(device_name(name))

    @app.get("/api/audit")
    @bearer(token)
    def audit():
        with database(admission.db) as db:
            rows = db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200").fetchall()
            return {"events": [dict(row) for row in rows]}

    @app.get('/api/operations')
    @bearer(token)
    def operations():
        return storage_summary(admission.db)

    @app.post("/api/challenge")
    def challenge():
        admission.throttle(request_ip())
        return admission.challenge(json_body("certificate", "wg_public_key"))

    @app.post("/api/verify")
    def verify():
        admission.throttle(request_ip())
        return admission.verify(
            json_body("challenge_id", "certificate", "wg_public_key", "signature")
        )

    return app


def request_ip():
    from flask import request

    return request.remote_addr or "unknown"


def daemon_main():
    parser = argparse.ArgumentParser(description="Remove expired/revoked/unknown VanGuard peers")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    admission = from_environment()
    # On every daemon restart require fresh admissions.
    admission.reconcile(startup=True)
    notify_supervisor('READY=1')
    while True:
        result = admission.reconcile()
        durable_write(admission.path / 'daemon-heartbeat.json', json.dumps({
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'monotonic': time.monotonic(), 'crl_available': result['crl_available'],
        }).encode())
        notify_supervisor('WATCHDOG=1')
        if args.once:
            return
        time.sleep(5)


def notify_supervisor(message):
    address = os.environ.get('NOTIFY_SOCKET')
    if address:
        if address.startswith('@'):
            address = '\0' + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
            channel.settimeout(1)
            channel.sendto(message.encode(), address)


if __name__ == "__main__":
    daemon_main()
