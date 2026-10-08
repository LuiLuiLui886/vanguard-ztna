import argparse
import functools
import getpass
import io
import json
import os
import secrets
import sqlite3
import time
from datetime import timedelta

import pyotp
from flask import flash, redirect, render_template, request, send_file, session, url_for
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
from .pki import check_csr


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
            """)

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

    def register(self, body):
        if not isinstance(body, dict) or not all(
            isinstance(body.get(k), str) for k in ("device_id", "csr", "wg_public_key", "tunnel_ip")
        ):
            raise Rejected("Invalid enrollment JSON")
        name = device_name(body["device_id"])
        wg_key(body["wg_public_key"])
        tunnel_ip(body["tunnel_ip"])
        check_csr(body["csr"], name)
        with locked(self.lock):
            try:
                with database(self.db) as db:
                    db.execute(
                        "INSERT INTO devices(device_id,request,status) VALUES (?,?,'pending_issue')",
                        (name, json.dumps(body, sort_keys=True)),
                    )
            except sqlite3.IntegrityError as exc:
                raise Rejected(
                    "Device already exists; use retry on the existing workflow", 409
                ) from exc
            self._enroll(name)

    def retry(self, name):
        with locked(self.lock):
            row = self.device(name)
            if row["status"] in ("revoking", "revoked"):
                self._revoke(name)
            elif row["status"] != "registered":
                self._enroll(name)

    def device(self, name):
        with database(self.db) as db:
            row = db.execute("SELECT * FROM devices WHERE device_id=?", (name,)).fetchone()
            if not row:
                raise Rejected("Unknown device", 404)
            return row

    def _enroll(self, name):
        row = self.device(name)
        body = json.loads(row["request"])
        try:
            if not row["certificate"]:
                result = self.ca.call(
                    "POST", "/api/ca/issue", {"device_id": name, "csr": body["csr"]}
                )
                with database(self.db) as db:
                    db.execute(
                        "UPDATE devices SET certificate=?,serial=?,status='pending_registry',last_error=NULL "
                        "WHERE device_id=?",
                        (result["certificate"], result["serial"], name),
                    )
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
            with database(self.db) as db:
                db.execute(
                    "UPDATE devices SET status='registered',last_error=NULL WHERE device_id=?",
                    (name,),
                )
        except Rejected as exc:
            self.error(name, exc)
            raise

    def error(self, name, exc):
        with database(self.db) as db:
            db.execute("UPDATE devices SET last_error=? WHERE device_id=?", (str(exc), name))

    def revoke(self, name):
        with locked(self.lock):
            row = self.device(name)
            if not row["certificate"]:
                raise Rejected("No certificate recorded; resolve issuance before revocation")
            with database(self.db) as db:
                db.execute("UPDATE devices SET status='revoking' WHERE device_id=?", (name,))
            self._revoke(name)

    def _revoke(self, name):
        row = self.device(name)
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
            self.error(name, exc)
            raise exc
        with database(self.db) as db:
            db.execute(
                "UPDATE devices SET status='revoked',last_error=NULL WHERE device_id=?", (name,)
            )


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
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        with database(dashboard.db) as db:
            db.execute("DELETE FROM sessions WHERE token=?", (session.get("token"),))
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        with database(dashboard.db) as db:
            devices = db.execute("SELECT * FROM devices ORDER BY device_id").fetchall()
        live, events, error = {}, [], None
        try:
            live = {
                d["device_id"]: d for d in dashboard.server.call("GET", "/api/devices")["devices"]
            }
            events = dashboard.server.call("GET", "/api/audit")["events"][:25]
        except Rejected as exc:
            error = str(exc)
        return render_template(
            "dashboard.html", devices=devices, live=live, events=events, error=error
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
            dashboard.register(body)
            flash("Sertifikat diterbitkan dan binding terdaftar. Client dapat memulai admission.")
        except Rejected as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    @app.post("/devices/<name>/<action>")
    @login_required
    def action(name, action):
        device_name(name)
        try:
            if action == "revoke":
                dashboard.revoke(name)
            elif action == "retry":
                dashboard.retry(name)
            else:
                raise Rejected("Unknown action", 404)
            flash("Operasi selesai.")
        except Rejected as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

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
