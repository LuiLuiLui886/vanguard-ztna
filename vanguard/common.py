import base64
import functools
import ipaddress
import os
import re
import secrets
import sqlite3
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import requests
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


class Rejected(Exception):
    def __init__(self, message, status=400, reason=None):
        self.detected_ns = time.monotonic_ns()
        super().__init__(message)
        self.status = status
        self.reason = reason


def required_secret(name):
    value = os.environ.get(name, "")
    if len(value) < 32:
        raise RuntimeError(f"{name} must contain at least 32 characters")
    return value


def private_dir(path):
    if os.name == 'nt':
        from .windows import check_private_path
        check_private_path(path)
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'nt':
        from .windows import protect_directory
        protect_directory(path)
    return path


def write_private(path, data):
    path = Path(path)
    if os.name == 'nt':
        private_dir(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(data.encode() if isinstance(data, str) else data)


def run(args, **kwargs):
    try:
        return subprocess.run(args, check=True, capture_output=True, timeout=30, **kwargs)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        # Do not put OpenSSL input, keys, tokens, or command output in API errors.
        raise Rejected("Local cryptographic/network operation failed", 503) from exc


@contextmanager
def locked(path):
    # CA/server locking is Linux-only; importing the client on Windows must work.
    if os.name == 'nt':
        raise Rejected('CA/server processes require Linux')
    import fcntl

    with open(path, "a", encoding="utf-8") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


@contextmanager
def database(path):
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def make_app(name):
    app = Flask(name)
    app.config.update(MAX_CONTENT_LENGTH=64 * 1024)

    @app.errorhandler(Rejected)
    def rejected(exc):
        return jsonify(error=str(exc)), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.name), exc.code

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok", "service": name}

    return app


def bearer(token):
    def decorate(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            supplied = request.headers.get("Authorization", "")
            if not secrets.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
                raise Rejected("Unauthorized", 401)
            return func(*args, **kwargs)

        return wrapped

    return decorate


def json_body(*fields):
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise Rejected("Expected JSON object")
    for field in fields:
        if not isinstance(body.get(field), str) or not body[field]:
            raise Rejected(f"Missing or invalid {field}")
    return body


def device_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", value):
        raise Rejected("Invalid device ID")
    return value


def wg_key(value):
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) != 32 or raw == bytes(32) or base64.b64encode(raw).decode() != value:
            raise ValueError()
    except (ValueError, TypeError) as exc:
        raise Rejected("Invalid WireGuard public key") from exc
    return value


def tunnel_ip(value):
    try:
        ip = ipaddress.IPv4Address(value)
        if ip not in ipaddress.IPv4Network("10.8.0.0/24") or ip.packed[-1] in (0, 1, 255):
            raise ValueError()
    except (ValueError, TypeError) as exc:
        raise Rejected("Invalid client tunnel address") from exc
    return str(ip)


class Remote:
    def __init__(self, url, trust, token=None):
        if not url.startswith("https://"):
            raise RuntimeError("VanGuard API URLs must use HTTPS")
        self.url, self.trust, self.token = url.rstrip("/"), str(trust), token

    def call(self, method, path, data=None, raw=False):
        headers = {"Authorization": "Bearer " + self.token} if self.token else {}
        try:
            response = requests.request(
                method,
                self.url + path,
                json=data,
                headers=headers,
                verify=self.trust,
                timeout=(3, 10),
                allow_redirects=False,
            )
            if not 200 <= response.status_code < 300:
                # Retain a safe upstream explanation without echoing submitted credentials.
                try:
                    message = response.json().get("error", "Upstream rejected request")
                except (ValueError, AttributeError):
                    message = "Upstream rejected request"
                error = Rejected(str(message)[:200], 502)
                error.upstream_status = response.status_code
                raise error
            return response.content if raw else response.json()
        except (requests.RequestException, ValueError, OSError) as exc:
            raise Rejected("Upstream unavailable or TLS validation failed", 503) from exc
