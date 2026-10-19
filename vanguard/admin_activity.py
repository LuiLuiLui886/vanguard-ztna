"""Readable administrator history and durable, authenticated archive snapshots."""

import csv
import hashlib
import io
import json
import math
import secrets
import time
import zipfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .common import Rejected, database

WIB = ZoneInfo('Asia/Jakarta')
PAGE_SIZE = 50
ARCHIVE_LIMIT = 10000
ARCHIVE_BYTES = 8 * 1024 * 1024
EVENTS = {
    'identity_replacement_requested': ('Penggantian identitas diminta', 'Identitas baru didaftarkan setelah pencabutan identitas lama; binding lama dipertahankan.'),
    'admin_login': ('Masuk dashboard', 'Administrator berhasil masuk dengan password dan TOTP.'),
    'admin_logout': ('Keluar dashboard', 'Administrator mengakhiri sesi dashboard.'),
    'registration_requested': ('Registrasi diminta', 'Permintaan registrasi perangkat disimpan untuk diproses.'),
    'certificate_issued': ('Sertifikat diterbitkan', 'CA berhasil menerbitkan sertifikat perangkat.'),
    'registration_completed': ('Registrasi selesai', 'Identitas dan binding perangkat terdaftar. Akses VPN tetap memerlukan admission.'),
    'workflow_retry': ('Proses diulang', 'Administrator meminta melanjutkan proses yang tersimpan.'),
    'workflow_failed': ('Proses belum selesai', 'Proses perangkat gagal diselesaikan. Periksa layanan terkait sebelum mengulang.'),
    'metadata_updated': ('Data perangkat diperbarui', 'Data keterangan perangkat disimpan.'),
    'employee_bound': ('Akun ditautkan', 'Akun karyawan ditautkan ke identitas perangkat.'),
    'revocation_requested': ('Pencabutan diminta', 'Permintaan pencabutan akses dan sertifikat disimpan.'),
    'revocation_completed': ('Pencabutan selesai', 'Akses dinonaktifkan dan sertifikat dicabut.'),
    'employee_created': ('Akun karyawan dibuat', 'Akun karyawan baru berhasil dibuat.'),
    'employee_disabled': ('Akun karyawan dinonaktifkan', 'Akun karyawan dinonaktifkan dan akses perangkat terkait dicabut.'),
    'bundle_downloaded': ('Bundle diunduh', 'Bundle onboarding publik disiapkan untuk diunduh.'),
    'certificate_downloaded': ('Sertifikat diunduh', 'Sertifikat publik disiapkan untuk diunduh.'),
    'history_viewed': ('Riwayat perangkat dibuka', 'Administrator membuka riwayat identitas perangkat.'),
    'dashboard_viewed': ('Dashboard dibuka', 'Administrator membuka ringkasan perangkat dan layanan.'),
    'activity_searched': ('Aktivitas ditelusuri', 'Administrator menelusuri catatan aktivitas.'),
    'archives_viewed': ('Daftar arsip dibuka', 'Administrator membuka daftar arsip aktivitas tersimpan.'),
    'operation_failed': ('Tindakan tidak selesai', 'Permintaan administrator ditolak atau gagal. Perubahan lintas layanan mungkin belum selesai; periksa status perangkat.'),
    'audit_archive_created': ('Arsip aktivitas dibuat', 'Salinan aktivitas disimpan sebagai arsip. Catatan sumber tetap dipertahankan.'),
    'audit_archive_downloaded': ('Arsip aktivitas diunduh', 'Integritas arsip diperiksa dan berkas disiapkan untuk diunduh.'),
    'security_rejected': ('Permintaan tidak valid', 'Permintaan perubahan ditolak karena pemeriksaan keamanan formulir gagal.'),
}
REASONS = {
    'device_lost': 'Perangkat hilang', 'suspected_compromise': 'Dugaan kompromi',
    'retired': 'Perangkat tidak digunakan lagi', 'access_change': 'Perubahan hak akses',
    'test_cleanup': 'Pembersihan pengujian', 'operator_request': 'Permintaan operator',
}
FIELDS = {'display_name': 'nama perangkat', 'department': 'departemen',
          'owner': 'pemilik', 'platform': 'platform'}
OPERATIONS = {'registration': 'registrasi perangkat', 'metadata': 'mengubah data perangkat',
              'replace': 'mengganti identitas',
              'employee': 'menautkan akun', 'revoke': 'mencabut akses', 'retry': 'mengulang proses',
              'employee_create': 'membuat akun karyawan', 'employee_disable': 'menonaktifkan akun',
              'bundle': 'mengunduh bundle', 'certificate': 'mengunduh sertifikat',
              'archive_create': 'membuat arsip', 'archive_download': 'mengunduh arsip'}
STATES = {'pending_issue': 'menunggu sertifikat', 'pending_register': 'menunggu registrasi',
          'registered': 'terdaftar', 'revoking': 'pencabutan berlangsung', 'revoked': 'dicabut'}


def local_time(value):
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value).timestamp()
        return datetime.fromtimestamp(value, WIB).strftime('%d/%m/%Y %H:%M:%S WIB')
    except (ValueError, TypeError, OverflowError, OSError):
        return 'Waktu tidak tersedia'


def present(row):
    """Project only known detail fields; never render arbitrary request data."""
    row = dict(row)
    try:
        detail = json.loads(row.get('detail', '{}'))
    except (ValueError, TypeError):
        detail = {}
    if not isinstance(detail, dict):
        detail = {}
    event = row.get('event', '')
    title, description = EVENTS.get(event, ('Aktivitas lain', 'Peristiwa tersimpan; keterangan jenis ini belum tersedia.'))
    extras = []
    for key, label in (('serial', 'Serial sertifikat'), ('username', 'Akun karyawan'),
                       ('replacement', 'Identitas pengganti'),
                       ('archive_id', 'Nomor arsip')):
        value = detail.get(key)
        if isinstance(value, str):
            extras.append(f'{label}: {value[:100]}.')
    if isinstance(detail.get('reason'), str) and detail['reason'] in REASONS:
        extras.append('Alasan: ' + REASONS[detail['reason']] + '.')
    if isinstance(detail.get('action'), str) and detail['action'] in OPERATIONS:
        extras.append('Tindakan: ' + OPERATIONS[detail['action']] + '.')
    if isinstance(detail.get('status'), str) and detail['status'] in STATES:
        extras.append('Status sebelumnya: ' + STATES[detail['status']] + '.')
    fields = detail.get('fields')
    if isinstance(fields, list):
        names = [FIELDS[f] for f in fields if isinstance(f, str) and f in FIELDS]
        extras.append('Bagian yang disimpan: ' + (', '.join(names) or 'tidak ada perubahan') + '.')
    filters = detail.get('filters')
    if isinstance(filters, dict):
        for key, label in (('start', 'Tanggal mulai'), ('end', 'Tanggal akhir'),
                           ('actor', 'Pelaku dicari'), ('device', 'Perangkat dicari')):
            value = filters.get(key)
            if isinstance(value, str) and value:
                extras.append(f'{label}: {value[:100]}.')
        selected_event = filters.get('event')
        if isinstance(selected_event, str) and selected_event:
            extras.append('Jenis tindakan: ' + EVENTS.get(selected_event,
                                                           ('Aktivitas lain', ''))[0] + '.')
    for key, label in (('http_status', 'Kode respons'), ('row_count', 'Jumlah catatan')):
        if type(detail.get(key)) is int:
            extras.append(f'{label}: {detail[key]}.')
    result = {k: row.get(k) for k in ('id', 'timestamp', 'actor', 'event', 'device_id')}
    result.update(time_wib=local_time(row.get('timestamp')), title=title,
                  description=' '.join([description, *extras]))
    return result


def server_description(row):
    descriptions = {
        'registered': 'Identitas perangkat terdaftar; belum mengaktifkan peer VPN.',
        'accepted': 'Akun dan perangkat lolos admission; akses VPN diberikan atau diperbarui.',
        'peer_removed': 'Peer VPN dihapus oleh pemeriksaan akses server.',
        'employee_created': 'Akun karyawan dibuat.', 'employee_bound': 'Akun ditautkan ke perangkat.',
        'employee_disabled': 'Akun dinonaktifkan.', 'employee_login': 'Login karyawan berhasil.',
        'admission_timing': 'Waktu deteksi dan respons penolakan admission dicatat.',
        'disabled': 'Identitas perangkat dinonaktifkan.',
        'employee_logout': 'Sesi karyawan diakhiri; challenge dan akses sesi tersebut dicabut.',
        'employee_logout_pending': 'Token sesi dicabut; penghapusan peer belum terkonfirmasi, perlu retry.',
    }
    return descriptions.get(row['event'], 'Peristiwa keamanan dicatat pada server.')


def filters_from(values):
    filters = {k: str(values.get(k, '')).strip() for k in ('start', 'end', 'actor', 'device', 'event')}
    if any(len(v) > 100 for v in filters.values()):
        raise Rejected('Filter terlalu panjang')
    boundaries = {}
    for key in ('start', 'end'):
        if filters[key]:
            try:
                date = datetime.strptime(filters[key], '%Y-%m-%d').replace(tzinfo=WIB)
                if key == 'end':
                    date += timedelta(days=1)
                boundaries[key] = date.timestamp()
            except (ValueError, OverflowError) as exc:
                raise Rejected('Tanggal filter harus valid, dengan format tahun-bulan-tanggal') from exc
    if 'start' in boundaries and 'end' in boundaries and boundaries['start'] >= boundaries['end']:
        raise Rejected('Tanggal akhir harus sama atau sesudah tanggal awal')
    if filters['event'] and filters['event'] not in EVENTS:
        raise Rejected('Jenis aktivitas tidak dikenal')
    parts, params = [], []
    for key, operator in (('start', '>='), ('end', '<')):
        if key in boundaries:
            parts.append('timestamp ' + operator + ' ?')
            params.append(boundaries[key])
    for key, column in (('actor', 'actor'), ('device', 'device_id'), ('event', 'event')):
        if filters[key]:
            parts.append(column + ' = ?')
            params.append(filters[key])
    return filters, (' WHERE ' + ' AND '.join(parts) if parts else ''), params


def page_number(value):
    try:
        page = int(value)
        if not 1 <= page <= 1000000:
            raise ValueError
        return page
    except (ValueError, TypeError) as exc:
        raise Rejected('Nomor halaman tidak valid') from exc


class ActivityArchive:
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.db = dashboard.db
        with database(self.db) as db:
            db.executescript('''
                CREATE INDEX IF NOT EXISTS admin_audit_time ON admin_audit(timestamp,id);
                CREATE INDEX IF NOT EXISTS admin_audit_actor ON admin_audit(actor,id);
                CREATE INDEX IF NOT EXISTS admin_audit_device ON admin_audit(device_id,id);
                CREATE TABLE IF NOT EXISTS admin_archives (
                    archive_id TEXT PRIMARY KEY, created_at REAL NOT NULL, actor TEXT NOT NULL,
                    filters TEXT NOT NULL, row_count INTEGER NOT NULL,
                    first_event_id INTEGER NOT NULL, last_event_id INTEGER NOT NULL,
                    sha256 TEXT NOT NULL, payload BLOB NOT NULL
                );
            ''')

    def history(self, values, page=1):
        filters, where, params = filters_from(values)
        page = page_number(page)
        with database(self.db) as db:
            db.execute('BEGIN')
            total = db.execute('SELECT count(*) FROM admin_audit' + where, params).fetchone()[0]
            rows = db.execute('SELECT * FROM admin_audit' + where + ' ORDER BY id DESC LIMIT ? OFFSET ?',
                              [*params, PAGE_SIZE, (page - 1) * PAGE_SIZE]).fetchall()
        return {'filters': filters, 'events': [present(r) for r in rows], 'total': total,
                'page': page, 'pages': max(1, math.ceil(total / PAGE_SIZE))}

    def listing(self, page=1):
        page = page_number(page)
        with database(self.db) as db:
            db.execute('BEGIN')
            total = db.execute('SELECT count(*) FROM admin_archives').fetchone()[0]
            rows = db.execute('SELECT archive_id,created_at,actor,filters,row_count,first_event_id,'
                              'last_event_id,sha256 FROM admin_archives ORDER BY created_at DESC,archive_id '
                              'LIMIT ? OFFSET ?', (PAGE_SIZE, (page - 1) * PAGE_SIZE)).fetchall()
        return {'archives': [dict(r, filters=json.loads(r['filters'])) for r in rows],
                'page': page, 'pages': max(1, math.ceil(total / PAGE_SIZE)), 'total': total}

    def create(self, values, actor):
        filters, where, params = filters_from(values)
        with database(self.db) as db:
            # Snapshot and its creation audit commit together; no source rows are moved/deleted.
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT * FROM admin_audit' + where + ' ORDER BY id LIMIT ?',
                              [*params, ARCHIVE_LIMIT + 1]).fetchall()
            if not rows:
                raise Rejected('Tidak ada aktivitas pada filter ini untuk diarsipkan')
            if len(rows) > ARCHIVE_LIMIT:
                raise Rejected('Arsip melebihi 10.000 catatan. Persempit rentang tanggal atau filter.')
            records = [present(r) for r in rows]
            at = time.time()
            archive_id = datetime.fromtimestamp(at, WIB).strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(6)
            manifest = {'schema': 1, 'archive_id': archive_id, 'created_at_utc': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                        'created_at_wib': local_time(at), 'created_by': actor, 'timezone': 'Asia/Jakarta',
                        'filters': filters, 'row_count': len(rows), 'first_event_id': rows[0]['id'],
                        'last_event_id': rows[-1]['id'], 'source': 'admin_audit',
                        'scope': 'Snapshot tindakan administrasi; bukan log admission server atau audit tahan manipulasi oleh root.'}
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            columns = ('id', 'time_wib', 'actor', 'title', 'device_id', 'description', 'event', 'timestamp')
            writer.writerow(('ID', 'Waktu WIB', 'Pelaku', 'Tindakan', 'Perangkat', 'Keterangan', 'Kode peristiwa', 'Timestamp UTC'))
            for record in records:
                cells = []
                for column in columns:
                    value = str(record[column] if record[column] is not None else '')
                    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
                        value = "'" + value
                    cells.append(value)
                writer.writerow(cells)
            files = {'aktivitas.csv': output.getvalue().encode('utf-8-sig'),
                     'aktivitas.json': json.dumps(records, ensure_ascii=False, indent=2).encode()}
            manifest['files_sha256'] = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
            files['manifest.json'] = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
            files['PETUNJUK.txt'] = (
                'Arsip aktivitas administrator VanGuard\n'
                'Buka aktivitas.csv dengan Excel/LibreOffice atau aktivitas.json untuk data terstruktur.\n'
                'Tanggal filter inklusif dalam WIB. Timestamp asli memakai detik Unix/UTC.\n'
                'Urutan berdasarkan ID pencatatan; satu tindakan dapat menghasilkan beberapa tahap.\n'
                'Arsip memuat seluruh hasil filter sampai snapshot diambil, bukan hanya halaman yang terlihat.\n'
                'Peristiwa pembuatan arsip ini dicatat setelah snapshot dan tidak termasuk dalam isinya.\n'
                'Kolom CSV berisiko formula diberi awalan apostrof. Tidak ada password, TOTP atau private key.\n'
                'Manifest berisi checksum CSV/JSON; cocokkan checksum ZIP dengan daftar arsip dashboard.\n'
                'Checksum mendeteksi perubahan berkas, bukan tanda tangan digital atau jaminan terhadap root.\n'
                'Simpan unduhan di lokasi privat. Backup database admin juga diperlukan; jangan unggah arsip ke GitHub.\n'
            ).encode()
            if sum(map(len, files.values())) > ARCHIVE_BYTES:
                raise Rejected('Ukuran arsip terlalu besar. Persempit filter.')
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as bundle:
                for name, content in files.items():
                    bundle.writestr(name, content)
            payload = buffer.getvalue()
            digest = hashlib.sha256(payload).hexdigest()
            db.execute('INSERT INTO admin_archives VALUES (?,?,?,?,?,?,?,?,?)',
                       (archive_id, at, actor, json.dumps(filters), len(rows), rows[0]['id'], rows[-1]['id'], digest, payload))
            self.dashboard.audit('audit_archive_created', detail={'archive_id': archive_id, 'row_count': len(rows)}, actor=actor, db=db)
        return archive_id

    def download(self, archive_id, actor):
        with database(self.db) as db:
            row = db.execute('SELECT payload,sha256 FROM admin_archives WHERE archive_id=?', (archive_id,)).fetchone()
            if not row:
                raise Rejected('Arsip tidak ditemukan', 404)
            if hashlib.sha256(row['payload']).hexdigest() != row['sha256']:
                raise Rejected('Integritas arsip tidak cocok. Periksa backup; unduhan dibatalkan.', 409)
            self.dashboard.audit('audit_archive_downloaded', detail={'archive_id': archive_id}, actor=actor, db=db)
        return row['payload'], row['sha256']
