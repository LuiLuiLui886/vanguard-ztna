import argparse
import functools
import getpass
import io
import json
import os
import secrets
import sqlite3
import time
import zipfile
from datetime import datetime, timedelta, timezone

import pyotp
from flask import flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .common import (
    Rejected,
    Remote,
    database,
    device_name,
    locked,
    make_app,
    private_dir,
    required_secret,
    tunnel_ip,
    wg_key,
)
from .pki import check_csr, fingerprint, load_cert, validate_certificate, validate_fetched_crl

DEVICE_METADATA = {"display_name": 100, "department": 80, "owner": 100, "platform": 80}
REVOCATION_REASONS = {
    'device_lost': 'Perangkat hilang', 'suspected_compromise': 'Dugaan kompromi',
    'retired': 'Perangkat tidak digunakan lagi', 'access_change': 'Perubahan hak akses',
    'test_cleanup': 'Pembersihan pengujian', 'operator_request': 'Permintaan operator',
}


def certificate_summary(pem):
    if not pem:
        return None
    try:
        cert = load_cert(pem)
        at = datetime.now(timezone.utc)
        status = ('Belum berlaku' if at < cert.not_valid_before_utc else
                  'Kedaluwarsa' if at >= cert.not_valid_after_utc else 'Dalam masa berlaku')
        return {'not_before': cert.not_valid_before_utc.isoformat(),
                'not_after': cert.not_valid_after_utc.isoformat(), 'status': status,
                'sha256': fingerprint(cert)}
    except Rejected:
        return {'status': 'Sertifikat tidak dapat dibaca'}


def device_metadata(value):
    if not isinstance(value, dict):
        raise Rejected("Data perangkat harus berupa objek")
    result = {}
    for field, maximum in DEVICE_METADATA.items():
        text = value.get(field)
        if not isinstance(text, str) or not text.strip() or len(text) > maximum:
            raise Rejected(f"Data {field} wajib diisi, maksimal {maximum} karakter")
        if any(ord(char) < 32 or ord(char) == 127 for char in text):
            raise Rejected(f"Data {field} mengandung karakter kontrol")
        result[field] = text.strip()
    return result


class Dashboard:
    def __init__(self, directory, ca, server):
        self.path = private_dir(directory)
        self.db = self.path / "admin.db"
        self.lock = self.path / "workflow.lock"
        self.ca, self.server = ca, server
        with database(self.db) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
                    totp_secret TEXT NOT NULL, last_step INTEGER NOT NULL DEFAULT -1
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY, username TEXT NOT NULL, expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY, request TEXT NOT NULL, certificate TEXT,
                    serial TEXT, status TEXT NOT NULL, last_error TEXT
                );
                CREATE TABLE IF NOT EXISTS admin_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
                    actor TEXT NOT NULL, event TEXT NOT NULL, device_id TEXT, detail TEXT NOT NULL
                );
            """)
            db.execute('BEGIN IMMEDIATE')
            columns = {r['name'] for r in db.execute('PRAGMA table_info(devices)')}
            for name, kind in (('revocation_reason', 'TEXT'), ('revoked_at', 'REAL')):
                if name not in columns:
                    db.execute(f'ALTER TABLE devices ADD COLUMN {name} {kind}')

    def audit(self, event, name=None, detail=None, actor='system', db=None):
        values = (time.time(), actor, event, name, json.dumps(detail or {}, sort_keys=True))
        statement = 'INSERT INTO admin_audit(timestamp,actor,event,device_id,detail) VALUES (?,?,?,?,?)'
        if db is not None:
            db.execute(statement, values)
        else:
            with database(self.db) as connection:
                connection.execute(statement, values)

    def history(self, name=None):
        with database(self.db) as db:
            query = 'SELECT * FROM admin_audit'
            params = ()
            if name is not None:
                query += ' WHERE device_id=?'
                params = (name,)
            return [dict(r) for r in db.execute(query + ' ORDER BY id DESC LIMIT 100', params)]

    def dependency_health(self):
        results = {}
        for name, remote in (('CA', self.ca), ('Server', self.server)):
            try:
                result = remote.call('GET', '/healthz')
                results[name] = ('Tersedia' if isinstance(result, dict) and result.get('status') == 'ok'
                                 else 'Tidak siap')
            except Rejected:
                results[name] = 'Tidak tersedia'
        return results

    def login(self, username, password, code, source):
        at = time.time()
        with database(self.db) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM attempts WHERE until < ?", (at,))
            buckets = ("ip:" + source, "user:" + username[:128])
            for bucket in buckets:
                row = db.execute("SELECT count FROM attempts WHERE bucket=?", (bucket,)).fetchone()
                if row and row[0] >= 5:
                    return None
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            valid = False
            step = int(at // 30)
            if user and check_password_hash(user["password_hash"], password):
                totp = pyotp.TOTP(user["totp_secret"])
                valid = step > user["last_step"] and secrets.compare_digest(
                    totp.at(at).encode(), code.encode()
                )
            if not valid:
                for bucket in buckets:
                    db.execute(
                        "INSERT INTO attempts VALUES (?,1,?) ON CONFLICT(bucket) "
                        "DO UPDATE SET count=count+1",
                        (bucket, at + 300),
                    )
                return None
            db.execute("UPDATE users SET last_step=? WHERE username=?", (step, username))
            token = secrets.token_urlsafe(32)
            db.execute("DELETE FROM sessions WHERE expires <= ?", (at,))
            db.execute("INSERT INTO sessions VALUES (?,?,?)", (token, username, at + 1800))
            return token

    def register(self, body, metadata=None, actor='system'):
        if not isinstance(body, dict) or not all(
            isinstance(body.get(k), str) for k in ("device_id", "csr", "wg_public_key", "tunnel_ip")
        ):
            raise Rejected("Invalid enrollment JSON")
        name = device_name(body["device_id"])
        wg_key(body["wg_public_key"])
        tunnel_ip(body["tunnel_ip"])
        check_csr(body["csr"], name)
        body = dict(body)
        if body.get('employee_username') is not None:
            body['employee_username'] = device_name(body['employee_username'])
        # Legacy client requests remain valid; the interactive form supplies metadata.
        supplied = metadata if metadata is not None else body.get("metadata")
        if supplied is not None:
            body["metadata"] = device_metadata(supplied)
        with locked(self.lock):
            try:
                with database(self.db) as db:
                    db.execute(
                        "INSERT INTO devices(device_id,request,status) VALUES (?,?,'pending_issue')",
                        (name, json.dumps(body, sort_keys=True)),
                    )
                    self.audit('registration_requested', name, actor=actor, db=db)
            except sqlite3.IntegrityError as exc:
                raise Rejected(
                    "Device already exists; use retry on the existing workflow", 409
                ) from exc
            self._enroll(name, actor)

    def update_metadata(self, name, metadata, actor='system'):
        metadata = device_metadata(metadata)
        with locked(self.lock), database(self.db) as db:
            row = db.execute("SELECT request FROM devices WHERE device_id=?", (name,)).fetchone()
            if not row:
                raise Rejected("Unknown device", 404)
            body = json.loads(row["request"])
            body["metadata"] = metadata
            db.execute("UPDATE devices SET request=? WHERE device_id=?",
                       (json.dumps(body, sort_keys=True), name))
            self.audit('metadata_updated', name, {'fields': sorted(metadata)}, actor, db)

    def bind_employee(self, name, username, actor='system'):
        username = device_name(username)
        with locked(self.lock):
            row = self.device(name)
            self.server.call('POST', f'/api/devices/{name}/employee', {'username': username})
            body = json.loads(row['request'])
            body['employee_username'] = username
            with database(self.db) as db:
                db.execute('UPDATE devices SET request=? WHERE device_id=?',
                           (json.dumps(body, sort_keys=True), name))
                self.audit('employee_bound', name, {'username': username}, actor, db)

    def retry(self, name, actor='system'):
        with locked(self.lock):
            row = self.device(name)
            self.audit('workflow_retry', name, {'status': row['status']}, actor)
            if row["status"] in ("revoking", "revoked"):
                self._revoke(name, actor)
            elif row["status"] != "registered":
                self._enroll(name, actor)

    def device(self, name):
        with database(self.db) as db:
            row = db.execute("SELECT * FROM devices WHERE device_id=?", (name,)).fetchone()
            if not row:
                raise Rejected("Unknown device", 404)
            return row

    def _enroll(self, name, actor='system'):
        row = self.device(name)
        body = json.loads(row["request"])
        try:
            if not row["certificate"]:
                health = self.ca.call('GET', '/healthz')
                if not isinstance(health, dict) or health.get('status') != 'ok':
                    raise Rejected('CA health check failed', 503)
                result = self.ca.call(
                    "POST", "/api/ca/issue", {"device_id": name, "csr": body["csr"]}
                )
                with database(self.db) as db:
                    db.execute(
                        "UPDATE devices SET certificate=?,serial=?,status='pending_registry',last_error=NULL "
                        "WHERE device_id=?",
                        (result["certificate"], result["serial"], name),
                    )
                    self.audit('certificate_issued', name, {'serial': result['serial']}, actor, db)
                row = self.device(name)
            self.server.call(
                "POST",
                "/api/devices",
                {
                    "device_id": name,
                    "certificate": row["certificate"],
                    "wg_public_key": body["wg_public_key"],
                    "tunnel_ip": body["tunnel_ip"],
                },
            )
            if body.get('employee_username'):
                self.server.call('POST', f'/api/devices/{name}/employee',
                                 {'username': device_name(body['employee_username'])})
            with database(self.db) as db:
                db.execute(
                    "UPDATE devices SET status='registered',last_error=NULL WHERE device_id=?",
                    (name,),
                )
                self.audit('registration_completed', name, {'serial': row['serial']}, actor, db)
        except Rejected as exc:
            self.error(name, exc, actor)
            raise

    def error(self, name, exc, actor='system'):
        with database(self.db) as db:
            db.execute("UPDATE devices SET last_error=? WHERE device_id=?", (str(exc), name))
            self.audit('workflow_failed', name, {'http_status': exc.status}, actor, db)

    def revoke(self, name, reason='operator_request', actor='system'):
        if reason not in REVOCATION_REASONS:
            raise Rejected('Pilih alasan pencabutan yang valid')
        with locked(self.lock):
            row = self.device(name)
            if not row["certificate"]:
                raise Rejected("No certificate recorded; resolve issuance before revocation")
            if row['status'] == 'revoked':
                return
            if row['status'] != 'revoking':
                with database(self.db) as db:
                    db.execute("UPDATE devices SET status='revoking',revocation_reason=? WHERE device_id=?",
                               (reason, name))
                    self.audit('revocation_requested', name, {'reason': reason, 'serial': row['serial']},
                               actor, db)
            self._revoke(name, actor)

    def _revoke(self, name, actor='system'):
        row = self.device(name)
        if row['status'] == 'revoked':
            return
        # Both operations are idempotent. Attempt CA revocation even if server is unreachable.
        failures = []
        for remote, path, body in (
            (self.server, f"/api/devices/{name}/disable", {}),
            (self.ca, "/api/ca/revoke", {"serial": row["serial"]}),
        ):
            try:
                remote.call("POST", path, body)
            except Rejected as exc:
                if not (remote is self.server and getattr(exc, "upstream_status", None) == 404):
                    failures.append(str(exc))
        if failures:
            exc = Rejected("; ".join(failures), 503)
            self.error(name, exc, actor)
            raise exc
        with database(self.db) as db:
            db.execute(
                "UPDATE devices SET status='revoked',revoked_at=?,last_error=NULL WHERE device_id=?",
                (time.time(), name),
            )
            self.audit('revocation_completed', name,
                       {'serial': row['serial'], 'reason': row['revocation_reason']}, actor, db)

    def bundle(self, name, actor='system'):
        with locked(self.lock):
            row = self.device(name)
            body = json.loads(row['request'])
            if row['status'] != 'registered' or not body.get('employee_username'):
                raise Rejected('Bundle memerlukan registrasi dan binding akun yang selesai', 409)
            root_pem = self.ca.call('GET', '/api/ca/certificate', raw=True)
            root = load_cert(root_pem)
            crl = validate_fetched_crl(root, self.ca.call('GET', '/api/ca/crl', raw=True))
            validate_certificate(root, row['certificate'], crl, name)
            manifest = {k: body[k] for k in ('device_id', 'wg_public_key', 'tunnel_ip', 'employee_username')}
            manifest.update(schema=1, server='https://192.168.100.20:8081',
                            wireguard_endpoint='192.168.100.20:51820',
                            certificate_sha256=fingerprint(load_cert(row['certificate'])),
                            root_sha256=fingerprint(root), admission_required=True)
            instructions = (
                'VanGuard onboarding bundle (Ubuntu 22.04)\n\n'
                'Verify device_id, certificate SHA-256 and Root CA fingerprint with your administrator.\n'
                'This bundle contains PUBLIC material only. Keep identity.key and wg.key on the original client.\n'
                'Install device.crt in the SAME private identity directory that created request.json (mode 0600).\n'
                'Use the trusted /etc/vanguard/root.crt; do not replace trust solely from an unverified download.\n'
                'manifest.json documents the binding; the current CLI does not import it automatically.\n'
                'Login: sudo /opt/vanguard/venv/bin/vanguard-client --directory IDENTITY_DIR login --username USERNAME\n'
                'Use the employee username from manifest.json; enter the password interactively.\n'
                'For the main 10.8.0.2 client, restart the configured vanguard-client service.\n'
                'Other tunnel IPs require a separately managed lab interface; admit alone does not create a tunnel.\n'
                'No static peer, private key, password or session token is included.\n'
                'Registration/download never grants VPN access. All admission checks remain mandatory.\n'
            )
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
                for path, value in {'device.crt': row['certificate'], 'root.crt': root_pem,
                                    'manifest.json': json.dumps(manifest, indent=2),
                                    'README.txt': instructions}.items():
                    archive.writestr(path, value)
            self.audit('bundle_downloaded', name, {'serial': row['serial']}, actor)
            return buffer.getvalue()


def create_app(config=None):
    config = config or {}
    app = make_app(__name__)
    app.config.update(
        SECRET_KEY=config.get("SECRET_KEY") or required_secret("VANGUARD_SESSION_SECRET"),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )
    dashboard = config.get("DASHBOARD")
    if dashboard is None:
        trust = os.environ.get("VANGUARD_ROOT_CERT", "/etc/vanguard/root.crt")
        dashboard = Dashboard(
            os.environ.get("VANGUARD_ADMIN_DIR", "/var/lib/vanguard/admin"),
            Remote(
                os.environ.get("VANGUARD_CA_URL", "https://192.168.100.10:8080"),
                trust,
                required_secret("VANGUARD_CA_TOKEN"),
            ),
            Remote(
                os.environ.get("VANGUARD_SERVER_URL", "https://192.168.100.20:8081"),
                trust,
                required_secret("VANGUARD_SERVER_TOKEN"),
            ),
        )
    app.extensions["dashboard"] = dashboard

    @app.before_request
    def csrf_check():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        if request.method == "POST" and not secrets.compare_digest(
            request.form.get("csrf", "").encode(), session["csrf"].encode()
        ):
            raise Rejected("CSRF check failed", 403)

    def login_required(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            with database(dashboard.db) as db:
                row = db.execute(
                    "SELECT * FROM sessions WHERE token=? AND expires>?",
                    (session.get("token", ""), time.time()),
                ).fetchone()
            if not row:
                return redirect(url_for("login"))
            g.admin_username = row['username']
            return func(*args, **kwargs)

        return wrapped

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            token = dashboard.login(
                request.form.get("username", ""),
                request.form.get("password", ""),
                request.form.get("totp", ""),
                request.remote_addr or "unknown",
            )
            if not token:
                flash(
                    "Login gagal. Periksa password/TOTP; setelah 5 kegagalan tunggu 5 menit.",
                    "error",
                )
                return render_template("login.html"), 401
            session.clear()
            session.update(token=token, csrf=secrets.token_urlsafe(32))
            session.permanent = True
            dashboard.audit('admin_login', actor=request.form['username'])
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        with database(dashboard.db) as db:
            db.execute("DELETE FROM sessions WHERE token=?", (session.get("token"),))
            dashboard.audit('admin_logout', actor=g.admin_username, db=db)
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        with database(dashboard.db) as db:
            devices = [dict(row) for row in db.execute("SELECT * FROM devices ORDER BY device_id")]
        for device in devices:
            device["metadata"] = json.loads(device["request"]).get("metadata", {})
            device['employee_username'] = json.loads(device['request']).get('employee_username')
            device['validity'] = certificate_summary(device['certificate'])
        live, events, error, employees = {}, [], None, []
        try:
            live = {
                d["device_id"]: d for d in dashboard.server.call("GET", "/api/devices")["devices"]
            }
            events = dashboard.server.call("GET", "/api/audit")["events"][:25]
            employees = dashboard.server.call('GET', '/api/employees')['employees']
        except Rejected as exc:
            error = str(exc)
        return render_template(
            "dashboard.html", devices=devices, live=live, events=events, error=error,
            employees=employees, dependencies=dashboard.dependency_health(),
            admin_events=dashboard.history()[:25], revocation_reasons=REVOCATION_REASONS,
        )

    @app.post("/devices")
    @login_required
    def register():
        try:
            uploaded = request.files.get("enrollment")
            if not uploaded:
                raise Rejected("Upload request.json dari client")
            try:
                body = json.load(uploaded)
            except (ValueError, UnicodeDecodeError) as exc:
                raise Rejected("Invalid enrollment JSON") from exc
            if not isinstance(body, dict):
                raise Rejected("Invalid enrollment JSON")
            body['employee_username'] = device_name(request.form.get('employee_username'))
            dashboard.register(body, {field: request.form.get(field) for field in DEVICE_METADATA},
                               actor=g.admin_username)
            flash("Sertifikat diterbitkan dan binding terdaftar. Client dapat memulai admission.")
        except Rejected as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    @app.post('/employees')
    @login_required
    def create_employee():
        try:
            dashboard.server.call('POST', '/api/employees', {
                'username': device_name(request.form.get('username')),
                'password': request.form.get('password', ''),
            })
            dashboard.audit('employee_created', detail={'username': request.form['username']},
                            actor=g.admin_username)
            flash('Akun karyawan dibuat. Daftarkan perangkat untuk akun tersebut.')
        except Rejected as exc:
            flash(str(exc), 'error')
        return redirect(url_for('index'))

    @app.post('/employees/<username>/disable')
    @login_required
    def disable_employee(username):
        try:
            dashboard.server.call('POST', f'/api/employees/{device_name(username)}/disable', {})
            dashboard.audit('employee_disabled', detail={'username': username}, actor=g.admin_username)
            flash('Akun karyawan dinonaktifkan dan akses perangkat dicabut.')
        except Rejected as exc:
            flash(str(exc), 'error')
        return redirect(url_for('index'))

    @app.post("/devices/<name>/<action>")
    @login_required
    def action(name, action):
        device_name(name)
        try:
            if action == "metadata":
                dashboard.update_metadata(
                    name, {field: request.form.get(field) for field in DEVICE_METADATA}, g.admin_username
                )
            elif action == 'employee':
                dashboard.bind_employee(name, request.form.get('username'), g.admin_username)
            elif action == "revoke":
                dashboard.revoke(name, request.form.get('reason'), g.admin_username)
            elif action == "retry":
                dashboard.retry(name, g.admin_username)
            else:
                raise Rejected("Unknown action", 404)
            flash("Operasi selesai.")
        except Rejected as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    @app.get('/devices/<name>/history')
    @login_required
    def history(name):
        row = dict(dashboard.device(device_name(name)))
        return render_template('device_history.html', device=row,
                               validity=certificate_summary(row['certificate']),
                               events=dashboard.history(name), reasons=REVOCATION_REASONS)

    @app.get('/devices/<name>/bundle')
    @login_required
    def bundle(name):
        name = device_name(name)
        return send_file(io.BytesIO(dashboard.bundle(name, g.admin_username)), as_attachment=True,
                         download_name=name + '-onboarding.zip', mimetype='application/zip')

    @app.get("/devices/<name>/certificate")
    @login_required
    def certificate(name):
        row = dashboard.device(device_name(name))
        if not row["certificate"]:
            raise Rejected("Certificate not issued", 404)
        return send_file(
            io.BytesIO(row["certificate"].encode()),
            as_attachment=True,
            download_name=name + ".crt",
            mimetype="application/x-pem-file",
        )

    return app


def main():
    parser = argparse.ArgumentParser(description="Create a VanGuard administrator locally")
    parser.add_argument("--directory", default="/var/lib/vanguard/admin")
    parser.add_argument("--username", default="admin")
    args = parser.parse_args()
    device_name(args.username)
    password = getpass.getpass("Password (minimum 12 characters): ")
    if len(password) < 12 or password != getpass.getpass("Repeat password: "):
        parser.error("Passwords must match and contain at least 12 characters")
    dashboard = Dashboard(args.directory, None, None)
    secret = pyotp.random_base32()
    print("Add this URI to your authenticator (keep it private):")
    print(pyotp.TOTP(secret).provisioning_uri(args.username, issuer_name="VanGuard"))
    if not pyotp.TOTP(secret).verify(getpass.getpass("Enter authenticator code to confirm: ")):
        parser.error("TOTP confirmation failed")
    with database(dashboard.db) as db:
        try:
            db.execute(
                "INSERT INTO users(username,password_hash,totp_secret) VALUES (?,?,?)",
                (args.username, generate_password_hash(password), secret),
            )
        except sqlite3.IntegrityError:
            parser.error("User exists; refusing to overwrite")
    print("Administrator created.")


if __name__ == "__main__":
    main()
