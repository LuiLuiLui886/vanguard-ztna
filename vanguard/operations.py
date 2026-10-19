"""Storage observations without deleting audit evidence or exposing row contents."""

import shutil
import time

from .common import database


def storage_summary(path):
    size = sum(p.stat().st_size for p in (path, path.with_name(path.name + '-wal'),
                                        path.with_name(path.name + '-journal')) if p.exists())
    free = shutil.disk_usage(path.parent).free
    with database(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS storage_observations ('
                   'timestamp REAL NOT NULL, database_bytes INTEGER NOT NULL, audit_rows INTEGER NOT NULL)')
        audit_table = 'audit' if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                           "AND name='audit'").fetchone() else 'admin_audit'
        count, oldest = db.execute(f'SELECT count(*),min(timestamp) FROM {audit_table}').fetchone()
        previous = db.execute('SELECT * FROM storage_observations ORDER BY timestamp DESC LIMIT 1').fetchone()
        at = time.time()
        if previous is None or at - previous['timestamp'] >= 3600:
            db.execute('INSERT INTO storage_observations VALUES (?,?,?)', (at, size, count))
    return {'database_bytes': size, 'audit_rows': count, 'oldest_audit_at': oldest,
            'free_disk_bytes': free, 'observed_at': at,
            'growth_bytes_since_sample': size - previous['database_bytes'] if previous else None,
            'sample_at': previous['timestamp'] if previous else None,
            'storage_warning': size >= 100 * 1024**2 or free < 100 * 1024**2,
            'automatic_deletion': False}
