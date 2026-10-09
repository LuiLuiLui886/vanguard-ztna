"""Local employee authentication; a session never grants device admission by itself."""

import hashlib
import secrets
import sqlite3
import time

from werkzeug.security import check_password_hash, generate_password_hash

from .common import Rejected, database, device_name


class Employees:
    session_seconds = 8 * 3600

    def __init__(self, path):
        self.db = path
        with database(path) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS employees (
                    username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS employee_devices (
                    device_id TEXT PRIMARY KEY REFERENCES devices(device_id),
                    username TEXT NOT NULL REFERENCES employees(username)
                );
                CREATE TABLE IF NOT EXISTS employee_sessions (
                    token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES employees(username),
                    expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS employee_challenges (
                    challenge_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS employee_leases (
                    device_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS employee_attempts (
                    bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL
                );
            """)
        self.dummy_hash = generate_password_hash(secrets.token_urlsafe(32))

    @staticmethod
    def token_hash(token):
        if not isinstance(token, str) or not 32 <= len(token) <= 128:
            raise Rejected("Employee session or device binding rejected", 403)
        return hashlib.sha256(token.encode()).hexdigest()

    def create(self, username, password):
        device_name(username)
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise Rejected("Employee password must contain 12 to 256 characters")
        hashed = generate_password_hash(password)
        try:
            with database(self.db) as db:
                db.execute("INSERT INTO employees(username,password_hash) VALUES (?,?)",
                           (username, hashed))
        except sqlite3.IntegrityError as exc:
            raise Rejected("Employee already exists", 409) from exc
        return {"username": username, "enabled": True}

    def listing(self):
        with database(self.db) as db:
            return [dict(row) for row in db.execute(
                "SELECT username,enabled FROM employees ORDER BY username")]

    def login(self, username, password, source):
        if not isinstance(username, str) or not isinstance(password, str) or len(password) > 256:
            raise Rejected("Employee login rejected", 401)
        at = time.time()
        buckets = ("user:" + username[:128], "ip:" + source)
        with database(self.db) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM employee_attempts WHERE until <= ?", (at,))
            for bucket in buckets:
                row = db.execute("SELECT count FROM employee_attempts WHERE bucket=?",
                                 (bucket,)).fetchone()
                if row and row[0] >= 5:
                    raise Rejected("Employee login temporarily locked", 429)
            user = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchone()
            password_ok = check_password_hash(user['password_hash'] if user else self.dummy_hash,
                                              password)
            valid = bool(user and user['enabled'] and password_ok)
            if not valid:
                for bucket in buckets:
                    db.execute("INSERT INTO employee_attempts VALUES (?,1,?) "
                               "ON CONFLICT(bucket) DO UPDATE SET count=count+1",
                               (bucket, at + 300))
            else:
                token = secrets.token_urlsafe(32)
                expires = at + self.session_seconds
                db.execute("DELETE FROM employee_sessions WHERE expires <= ?", (at,))
                db.execute("INSERT INTO employee_sessions VALUES (?,?,?)",
                           (self.token_hash(token), username, expires))
        # Raise after committing failed attempts.
        if not valid:
            raise Rejected("Employee login rejected", 401)
        return {"session_token": token, "username": username, "expires_at": expires}

    def require_hash(self, hashed, device_id):
        with database(self.db) as db:
            row = db.execute(
                "SELECT s.username,s.expires FROM employee_sessions s "
                "JOIN employees e ON e.username=s.username "
                "JOIN employee_devices d ON d.username=e.username "
                "WHERE s.token_hash=? AND d.device_id=? AND e.enabled=1 AND s.expires>?",
                (hashed, device_id, time.time()),
            ).fetchone()
        if not row:
            raise Rejected("Employee session or device binding rejected", 403,
                           "employee_session_invalid")
        return dict(row)

    def require(self, token, device_id):
        hashed = self.token_hash(token)
        return hashed, self.require_hash(hashed, device_id)

    def bind(self, device_id, username):
        with database(self.db) as db:
            user = db.execute("SELECT enabled FROM employees WHERE username=?",
                              (username,)).fetchone()
            device = db.execute("SELECT enabled FROM devices WHERE device_id=?",
                                (device_id,)).fetchone()
            if not user or not user[0] or not device or not device[0]:
                raise Rejected("Active employee and device required", 409)
            old = db.execute("SELECT username FROM employee_devices WHERE device_id=?",
                             (device_id,)).fetchone()
            if old and old[0] != username:
                raise Rejected("Employee binding is immutable; revoke and enroll a new identity", 409)
            db.execute("INSERT OR IGNORE INTO employee_devices VALUES (?,?)", (device_id, username))
        return {"device_id": device_id, "username": username}

    def disable(self, username):
        with database(self.db) as db:
            if not db.execute("SELECT 1 FROM employees WHERE username=?", (username,)).fetchone():
                raise Rejected("Unknown employee", 404)
            db.execute("UPDATE employees SET enabled=0 WHERE username=?", (username,))
            db.execute("DELETE FROM employee_sessions WHERE username=?", (username,))
        return {"username": username, "enabled": False}
