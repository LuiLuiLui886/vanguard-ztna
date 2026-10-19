import io
import json
import time
import zipfile
from types import SimpleNamespace

import pyotp
import pytest
from conftest import LocalRemote
from werkzeug.security import generate_password_hash

from vanguard.admin import Dashboard, create_app
from vanguard.admin_activity import ActivityArchive, filters_from, local_time, present
from vanguard.ca import create_app as ca_app
from vanguard.common import Rejected, database

METADATA = {"display_name": "Laptop Produksi", "department": "Produksi",
            "owner": "Karyawan Uji", "platform": "Ubuntu 22.04"}


@pytest.fixture
def dashboard(lab, tmp_path):
    authority = ca_app({"CA_DIR": lab["ca"].path, "TOKEN": "c" * 32})
    dash = Dashboard(tmp_path / "admin", LocalRemote(authority, "c" * 32), lab["management"])
    secret = pyotp.random_base32()
    with database(dash.db) as db:
        db.execute(
            "INSERT INTO users(username,password_hash,totp_secret) VALUES (?,?,?)",
            ("admin", generate_password_hash("test-password-long"), secret),
        )
    app = create_app({"DASHBOARD": dash, "SECRET_KEY": "x" * 32})
    app.config["TESTING"] = True
    return dash, app.test_client(), secret


def csrf(client):
    client.get("/login", base_url="https://localhost")
    with client.session_transaction() as state:
        return state["csrf"]


def login(client, secret, code=None):
    return client.post(
        "/login",
        base_url="https://localhost",
        data={
            "csrf": csrf(client),
            "username": "admin",
            "password": "test-password-long",
            "totp": code or pyotp.TOTP(secret).now(),
        },
    )


def test_requires_login_and_csrf(dashboard):
    _, client, _ = dashboard
    assert client.get("/", base_url="https://localhost").status_code == 302
    assert client.post("/devices", base_url="https://localhost").status_code == 403


def test_login_requires_totp_and_rejects_replay(dashboard, monkeypatch):
    _, client, secret = dashboard
    at = time.time()
    monkeypatch.setattr("vanguard.admin.time", SimpleNamespace(time=lambda: at))
    code = pyotp.TOTP(secret).at(at)
    response = client.post(
        "/login",
        base_url="https://localhost",
        data={
            "csrf": csrf(client),
            "username": "admin",
            "password": "test-password-long",
            "totp": "invalid",
        },
    )
    assert response.status_code == 401
    assert login(client, secret, code).status_code == 302
    assert client.get("/", base_url="https://localhost").status_code == 200
    assert login(client, secret, code).status_code == 401


def test_lockout_persists(dashboard):
    dash, _, secret = dashboard
    for _ in range(5):
        assert dash.login("admin", "wrong", "wrong", "127.0.0.1") is None
    assert dash.login("admin", "test-password-long", pyotp.TOTP(secret).now(), "127.0.0.1") is None


def test_dashboard_enrollment_revocation_and_logout(lab, dashboard):
    dash, client, secret = dashboard
    assert login(client, secret).status_code == 302
    with client.session_transaction() as state:
        token = state["csrf"]
    response = client.post(
        "/devices",
        base_url="https://localhost",
        data={
            "csrf": token,
            "enrollment": (io.BytesIO(json.dumps(lab["request"]).encode()), "request.json"),
            **METADATA,
            'employee_username': 'employee-test',
        },
    )
    assert response.status_code == 302
    assert dash.device("vm-client")["status"] == "registered"
    assert json.loads(dash.device("vm-client")["request"])["metadata"] == METADATA
    assert lab["wg"].additions == []
    assert (
        client.get("/devices/vm-client/certificate", base_url="https://localhost").status_code
        == 200
    )
    response = client.post(
        "/devices/vm-client/revoke", base_url="https://localhost",
        data={"csrf": token, "reason": "test_cleanup"}
    )
    assert response.status_code == 302
    assert dash.device("vm-client")["status"] == "revoked"
    client.post("/logout", base_url="https://localhost", data={"csrf": token})
    assert client.get("/", base_url="https://localhost").status_code == 302


def test_partial_registration_retries_without_second_certificate(lab, dashboard):
    dash, _, _ = dashboard
    original = dash.server

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected("Offline", 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.register(lab["request"])
    row = dash.device("vm-client")
    assert row["status"] == "pending_registry"
    assert not lab["wg"].active
    dash.server = original
    dash.retry("vm-client")
    assert dash.device("vm-client")["serial"] == row["serial"]
    assert dash.device("vm-client")["status"] == "registered"


def test_ca_revocation_still_attempted_when_server_offline(lab, dashboard):
    dash, _, _ = dashboard
    dash.register(lab["request"])

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected("Offline", 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.revoke("vm-client")
    assert dash.device("vm-client")["status"] == "revoking"
    from vanguard.pki import validate_crl

    crl = validate_crl(lab["admission"].root, lab["ca"].crl())
    assert crl.get_revoked_certificate_by_serial_number(int(lab["issued"]["serial"], 16))


def test_legacy_metadata_edit_preserves_identity_and_escapes_html(lab, dashboard):
    dash, client, secret = dashboard
    dash.register(lab["request"])
    before = dict(dash.device("vm-client"))
    assert client.post('/devices/vm-client/metadata', base_url='https://localhost',
                       data={'csrf': csrf(client), **METADATA}).status_code == 302
    assert dash.device("vm-client")["request"] == before["request"]
    assert login(client, secret).status_code == 302
    with client.session_transaction() as state:
        token = state["csrf"]
    assert b'Belum diisi' in client.get('/', base_url='https://localhost').data
    response = client.post('/devices/vm-client/metadata', base_url='https://localhost',
                           data=METADATA)
    assert response.status_code == 403
    metadata = {**METADATA, 'display_name': '<script>alert(1)</script>'}
    assert client.post('/devices/vm-client/metadata', base_url='https://localhost',
                       data={'csrf': token, **metadata}).status_code == 302
    reloaded = Dashboard(dash.path, dash.ca, dash.server)
    after = dict(reloaded.device("vm-client"))
    request = json.loads(after.pop("request"))
    assert request.pop("metadata") == metadata
    assert request == json.loads(before.pop("request"))
    assert after == before  # No certificate, serial, workflow or identity changes.
    assert lab["wg"].additions == []
    page = client.get('/', base_url='https://localhost').data
    assert b'&lt;script&gt;' in page and b'<script>alert(1)</script>' not in page


@pytest.mark.parametrize('metadata', [
    None, {}, {**METADATA, 'owner': ''}, {**METADATA, 'owner': 'a' * 101},
    {**METADATA, 'platform': []}, {**METADATA, 'department': 'QA\nAdmin'},
])
def test_invalid_metadata_cannot_change_existing_identity(lab, dashboard, metadata):
    dash, _, _ = dashboard
    dash.register(lab["request"])
    before = dict(dash.device('vm-client'))
    with pytest.raises(Rejected):
        dash.update_metadata('vm-client', metadata)
    assert dict(dash.device('vm-client')) == before
    assert lab['wg'].additions == []


def test_metadata_survives_registry_retry(lab, dashboard):
    dash, _, _ = dashboard
    server = dash.server

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected('Offline', 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.register(lab['request'], METADATA)
    serial = dash.device('vm-client')['serial']
    dash.server = server
    dash.retry('vm-client')
    assert dash.device('vm-client')['serial'] == serial
    assert json.loads(dash.device('vm-client')['request'])['metadata'] == METADATA
    assert lab['wg'].additions == []


def test_admin_manages_employee_and_binds_legacy_device(lab, dashboard):
    dash, client, secret = dashboard
    legacy = {k: v for k, v in lab['request'].items() if k != 'employee_username'}
    dash.register(legacy)
    assert login(client, secret).status_code == 302
    with client.session_transaction() as state:
        token = state['csrf']
    assert client.post('/employees', base_url='https://localhost', data={
        'username': 'production-user', 'password': 'production-test-password',
    }).status_code == 403
    response = client.post('/employees', base_url='https://localhost', data={
        'csrf': token, 'username': 'production-user', 'password': 'production-test-password',
    })
    assert response.status_code == 302
    assert any(e['username'] == 'production-user' for e in lab['admission'].employees.listing())
    response = client.post('/devices/vm-client/employee', base_url='https://localhost', data={
        'csrf': token, 'username': 'production-user',
    })
    assert response.status_code == 302
    assert json.loads(dash.device('vm-client')['request'])['employee_username'] == 'production-user'
    assert lab['wg'].additions == []
    assert client.post('/employees/production-user/disable', base_url='https://localhost',
                       data={'csrf': token}).status_code == 302
    assert next(e for e in lab['admission'].employees.listing()
                if e['username'] == 'production-user')['enabled'] == 0


def test_health_is_independent_and_issuance_fails_closed(lab, dashboard):
    dash, client, secret = dashboard
    ca = dash.ca

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected('Offline', 503)

    dash.ca = Offline()
    assert dash.dependency_health() == {'CA': 'Tidak tersedia', 'Server': 'Tersedia'}
    with pytest.raises(Rejected):
        dash.register(lab['request'], actor='admin')
    assert dash.device('vm-client')['certificate'] is None
    assert dash.device('vm-client')['status'] == 'pending_issue'
    assert not lab['wg'].additions
    dash.ca = ca
    dash.retry('vm-client', actor='admin')
    assert dash.device('vm-client')['status'] == 'registered'
    dash.server = Offline()
    assert login(client, secret).status_code == 302
    page = client.get('/', base_url='https://localhost')
    assert page.status_code == 200 and b'Status server tidak tersedia' in page.data
    assert dash.dependency_health() == {'CA': 'Tersedia', 'Server': 'Tidak tersedia'}


def test_revocation_reason_survives_retry_and_is_audited_once(lab, dashboard):
    dash, _, _ = dashboard
    dash.register(lab['request'], actor='alice')
    server = dash.server

    class Offline:
        def call(self, *args, **kwargs):
            raise Rejected('Offline', 503)

    dash.server = Offline()
    with pytest.raises(Rejected):
        dash.revoke('vm-client', 'device_lost', actor='alice')
    assert dash.device('vm-client')['revocation_reason'] == 'device_lost'
    assert dash.device('vm-client')['revoked_at'] is None
    dash.server = server
    dash.retry('vm-client', actor='bob')
    row = dict(dash.device('vm-client'))
    assert row['status'] == 'revoked' and row['revoked_at'] > 0
    dash.revoke('vm-client', 'retired', actor='bob')
    assert dict(dash.device('vm-client')) == row
    events = dash.history('vm-client')
    requested = [e for e in events if e['event'] == 'revocation_requested']
    completed = [e for e in events if e['event'] == 'revocation_completed']
    assert len(requested) == len(completed) == 1
    assert requested[0]['actor'] == 'alice' and completed[0]['actor'] == 'bob'
    assert json.loads(completed[0]['detail'])['reason'] == 'device_lost'


def test_reason_required_and_actor_comes_from_authenticated_session(lab, dashboard):
    dash, client, secret = dashboard
    dash.register(lab['request'])
    assert login(client, secret).status_code == 302
    with client.session_transaction() as state:
        token = state['csrf']
    client.post('/devices/vm-client/revoke', base_url='https://localhost', data={'csrf': token})
    assert dash.device('vm-client')['status'] == 'registered'
    client.post('/devices/vm-client/revoke', base_url='https://localhost', data={
        'csrf': token, 'reason': 'test_cleanup', 'actor': 'forged',
    })
    assert dash.device('vm-client')['status'] == 'revoked'
    event = next(e for e in dash.history() if e['event'] == 'revocation_requested')
    assert event['actor'] == 'admin'
    assert 'forged' not in json.dumps(dash.history())


def test_bundle_is_public_only_and_does_not_admit(lab, dashboard):
    dash, client, secret = dashboard
    dash.register(lab['request'])
    for path in ('bundle', 'history'):
        assert client.get('/devices/vm-client/' + path, base_url='https://localhost').status_code == 302
    assert login(client, secret).status_code == 302
    response = client.get('/devices/vm-client/bundle', base_url='https://localhost')
    assert response.status_code == 200 and response.headers['Cache-Control'] == 'no-store'
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert set(archive.namelist()) == {'device.crt', 'root.crt', 'manifest.json', 'README.txt'}
        assert archive.read('device.crt').decode() == lab['issued']['certificate']
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['admission_required'] is True
        assert manifest['employee_username'] == 'employee-test'
        contents = b'\n'.join(archive.read(name) for name in archive.namelist())
        assert b'PRIVATE KEY-----' not in contents
        assert lab['employee_session'].encode() not in contents
        assert secret.encode() not in contents and b'employee-test-password' not in contents
        assert (lab['directory'] / 'wg.key').read_bytes().strip() not in contents
    assert not lab['wg'].additions
    page = client.get('/devices/vm-client/history', base_url='https://localhost')
    assert page.status_code == 200 and b'Bundle diunduh' in page.data
    assert b'Akhir berlaku' in page.data
    assert secret not in json.dumps(dash.history())


def test_bundle_refuses_ca_only_revocation_and_partial_workflow(lab, dashboard):
    dash, _, _ = dashboard
    dash.register(lab['request'])
    lab['ca'].revoke(dash.device('vm-client')['serial'])
    with pytest.raises(Rejected):
        dash.bundle('vm-client')
    assert not any(e['event'] == 'bundle_downloaded' for e in dash.history())
    assert not lab['wg'].additions


def test_upgrade_preserves_legacy_identity_and_does_not_invent_history(lab, tmp_path):
    path = tmp_path / 'legacy-admin'
    path.mkdir()
    with database(path / 'admin.db') as db:
        db.execute('CREATE TABLE devices (device_id TEXT PRIMARY KEY, request TEXT NOT NULL, '
                   'certificate TEXT, serial TEXT, status TEXT NOT NULL, last_error TEXT)')
        db.execute('INSERT INTO devices VALUES (?,?,?,?,?,?)', ('vm-client', json.dumps(lab['request']),
                   lab['issued']['certificate'], lab['issued']['serial'], 'registered', None))
    dash = Dashboard(path, None, None)
    row = dash.device('vm-client')
    assert row['certificate'] == lab['issued']['certificate']
    assert row['revocation_reason'] is None and row['revoked_at'] is None
    assert dash.history() == []
    again = Dashboard(path, None, None)
    assert dict(again.device('vm-client')) == dict(row)


def test_activity_time_wib_and_readable_whitelisted_details(dashboard):
    dash, _, _ = dashboard
    dash.audit('revocation_requested', 'vm-client',
               {'reason': 'device_lost', 'password': 'must never display'}, 'admin')
    row = present(dash.history('vm-client')[0])
    assert row['title'] == 'Pencabutan diminta'
    assert 'Perangkat hilang' in row['description']
    assert 'must never display' not in json.dumps(row)
    assert 'password' not in json.dumps(row)
    assert local_time(0) == '01/01/1970 07:00:00 WIB'


def test_activity_filters_use_inclusive_wib_dates_and_exact_admin(dashboard):
    dash, _, _ = dashboard
    dash.audit('admin_login', actor='admin')
    filters, where, params = filters_from({'start': '2026-10-12', 'end': '2026-10-12',
                                           'actor': 'admin', 'event': 'admin_login'})
    assert filters['actor'] == 'admin'
    assert 'timestamp >= ?' in where and 'timestamp < ?' in where
    assert params[0] < params[1] and len(params) == 4
    with pytest.raises(Rejected):
        filters_from({'start': '2026-13-01'})
    with pytest.raises(Rejected):
        filters_from({'start': '2026-10-13', 'end': '2026-10-12'})
    filters, where, params = filters_from({'actor': "' OR 1=1 --"})
    assert "' OR 1=1 --" in params and 'actor = ?' in where


def test_activity_page_and_archive_are_persistent_filter_complete_and_checksummed(dashboard):
    dash, client, secret = dashboard
    assert login(client, secret).status_code == 302
    for n in range(57):
        dash.audit('metadata_updated', f'device-{n % 2}', {'fields': ['owner']}, 'admin')
    archive = ActivityArchive(dash)
    page = archive.history({}, 2)
    assert page['total'] == 58  # Includes the authenticated admin login.
    assert len(page['events']) == 8
    archive_id = archive.create({'device': 'device-1'}, 'admin')
    row = archive.listing()['archives'][0]
    assert row['archive_id'] == archive_id and row['row_count'] == 28
    payload, digest = archive.download(archive_id, 'admin')
    assert __import__('hashlib').sha256(payload).hexdigest() == digest == row['sha256']
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        assert manifest['row_count'] == 28 and manifest['created_by'] == 'admin'
        assert 'activity.csv' not in bundle.namelist()
        csv_content = bundle.read('aktivitas.csv').decode('utf-8-sig')
        assert 'Waktu WIB' in csv_content and 'Data perangkat diperbarui' in csv_content
        assert 'must never' not in csv_content
    assert len(dash.history()) == 60  # Source events plus archive create/download audits.


def test_activity_archive_http_access_csrf_download_and_integrity(dashboard):
    dash, client, secret = dashboard
    assert client.get('/activity', base_url='https://localhost').status_code == 302
    assert client.get('/activity/archives', base_url='https://localhost').status_code == 302
    assert client.post('/activity/archives', base_url='https://localhost').status_code == 403
    assert login(client, secret).status_code == 302
    activity_page = client.get('/activity', base_url='https://localhost')
    assert activity_page.status_code == 200 and b'Aktivitas ditelusuri' in activity_page.data
    assert client.get('/activity/archives', base_url='https://localhost').status_code == 200
    with client.session_transaction() as state:
        token = state['csrf']
    for action in ('admin_login', 'admin_login'):
        dash.audit(action, actor='admin')
    response = client.post('/activity/archives', base_url='https://localhost',
                           data={'csrf': token, 'actor': 'admin'})
    assert response.status_code == 302
    with database(dash.db) as db:
        archive_id = db.execute('SELECT archive_id FROM admin_archives').fetchone()[0]
    payload = ActivityArchive(dash).download(archive_id, 'admin')[0]
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        events = json.loads(bundle.read('aktivitas.json'))
    assert any(event['title'] == 'Aktivitas ditelusuri' for event in events)
    response = client.get(f'/activity/archives/{archive_id}/download', base_url='https://localhost')
    assert response.status_code == 200
    assert response.headers['X-Archive-SHA256']
    with database(dash.db) as db:
        db.execute('UPDATE admin_archives SET payload=? WHERE archive_id=?', (b'corrupt', archive_id))
    response = client.get(f'/activity/archives/{archive_id}/download', base_url='https://localhost')
    assert response.status_code == 409
    assert any(e['event'] == 'operation_failed' for e in dash.history())


def test_csv_archive_neutralizes_formula_cells(dashboard):
    dash, _, _ = dashboard
    dash.audit('metadata_updated', 'device-1', {'fields': ['owner']}, '=2+3')
    archive_id = ActivityArchive(dash).create({}, 'admin')
    payload, _ = ActivityArchive(dash).download(archive_id, 'admin')
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        assert "'=2+3" in bundle.read('aktivitas.csv').decode('utf-8-sig')


def test_identity_replacement_preserves_old_binding_and_requires_revocation(lab, dashboard, tmp_path):
    from vanguard.client import initialize
    dash, client, secret = dashboard
    dash.register(lab['request'], METADATA)
    request = json.loads(initialize(tmp_path / 'replacement', 'replacement-client').read_text())
    with pytest.raises(Rejected, match='pencabutan'):
        dash.register(request, replaces='vm-client')
    old = dict(dash.device('vm-client'))
    dash.revoke('vm-client')
    dash.register(request, replaces='vm-client')
    assert dash.device('vm-client')['certificate'] == old['certificate']
    assert dash.device('vm-client')['status'] == 'revoked'
    assert dash.device('replacement-client')['status'] == 'registered'
    with database(lab['admission'].db) as db:
        bindings = dict(db.execute('SELECT device_id,username FROM employee_devices').fetchall())
    assert bindings['vm-client'] == bindings['replacement-client'] == 'employee-test'
    assert not lab['wg'].active  # enrollment never grants a peer
    assert login(client, secret).status_code == 302
    page = client.get('/devices/vm-client/history', base_url='https://localhost')
    assert page.status_code == 200 and b'Penggantian identitas' in page.data


def test_expiry_warning_is_separate_from_validity(lab, monkeypatch):
    from datetime import datetime, timedelta

    from vanguard import admin
    from vanguard.pki import load_cert
    expiry = load_cert(lab['issued']['certificate']).not_valid_after_utc
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return expiry - timedelta(days=3)
    monkeypatch.setattr(admin, 'datetime', Clock)
    summary = admin.certificate_summary(lab['issued']['certificate'])
    assert summary['expiring_soon'] is True and summary['days_remaining'] == 3
    assert summary['status'] == 'Dalam masa berlaku'


def test_operations_is_authenticated_and_preserves_audit(dashboard):
    dash, client, secret = dashboard
    assert client.get('/operations', base_url='https://localhost').status_code == 302
    assert login(client, secret).status_code == 302
    dash.audit('dashboard_viewed', actor='admin')
    before = dash.history()
    page = client.get('/operations', base_url='https://localhost')
    assert page.status_code == 200 and b'Tidak diketahui' not in page.data
    assert dash.history() == before
