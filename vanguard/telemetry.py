"""Request-local denial timing; never record credentials or caller-chosen IDs."""

import json
import re
import secrets
import time

from flask import g, jsonify, request

from .common import Rejected


def install_denial_timing(app, audit):
    @app.before_request
    def start_timing():
        if request.endpoint in ('challenge', 'verify'):
            g.admission_started_ns = time.monotonic_ns()
            g.admission_request_id = secrets.token_hex(16)

    @app.errorhandler(Rejected)
    def rejected(exc):
        if hasattr(g, 'admission_started_ns'):
            g.admission_rejection = exc
        return jsonify(error=str(exc)), exc.status

    @app.after_request
    def record_timing(response):
        if not hasattr(g, 'admission_request_id'):
            return response
        response.headers['X-VanGuard-Request-ID'] = g.admission_request_id
        exc = getattr(g, 'admission_rejection', None)
        if exc is None or response.status_code != exc.status or exc.status not in (400, 403):
            return response
        # Endpoint policy audit and JSON response construction have completed.
        # Telemetry persistence, final HTTP headers and network delivery follow.
        ready = time.monotonic_ns()
        start, detected = g.admission_started_ns, exc.detected_ns
        if not start <= detected <= ready:
            return response  # Never manufacture timing for an old exception object.
        reason = exc.reason if isinstance(exc.reason, str) and re.fullmatch(
            r'[a-z_]{1,64}', exc.reason) else 'policy_rejected'
        audit('admission_timing', None, json.dumps({
            'schema': 1, 'request_id': g.admission_request_id,
            'endpoint': request.endpoint, 'status': response.status_code, 'reason': reason,
            'detect_ns': detected - start,
            'respond_ns': ready - detected,
            'total_ns': ready - start,
            'clock': 'server_monotonic',
            'response_boundary': 'json_ready_before_telemetry_persistence',
        }, sort_keys=True))
        return response
