#!/usr/bin/env python3
"""Verify dashboard activity search, archive snapshot and download over HTTPS."""

import argparse
import hashlib
import html.parser
import io
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pyotp
import requests


class Forms(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name') == 'csrf':
            self.values[attrs.get('name')] = attrs.get('value')
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])


def parse(response):
    parser = Forms()
    parser.feed(response.text)
    return parser


def assert_no_credentials(bundle, credentials):
    # Compression can hide a verbatim secret in the ZIP container.
    # Inspect every member, including the manifest and future formats.
    for name in bundle.namelist():
        content = bundle.read(name)
        assert credentials['password'].encode() not in content
        assert credentials['totp_secret'].encode() not in content


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('onboarding', type=Path)
    cli.add_argument('--trust', type=Path, default=Path('state/deployment/root.crt'))
    cli.add_argument('--state', type=Path, required=True)
    args = cli.parse_args()
    os.umask(0o077)
    args.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    archive_path = args.state / 'admin-activity.zip'
    report_path = args.state / 'activity-verification.json'
    if archive_path.exists() or report_path.exists():
        cli.error('Evidence exists; choose a new --state directory')
    credentials = json.loads(args.onboarding.read_text())
    base = 'https://192.168.100.40:5000'
    session = requests.Session()
    session.verify = str(args.trust)
    report = {'status': 'RUNNING', 'checks': []}

    def record(name, passed=True):
        if not passed:
            raise RuntimeError('Verification failed: ' + name)
        report['checks'].append({'name': name, 'status': 'PASS'})
        report_path.write_text(json.dumps(report, indent=2) + '\n')

    try:
        page = session.get(base + '/login', timeout=15)
        form = parse(page)
        assert page.status_code == 200 and form.values.get('csrf')
        code = pyotp.TOTP(credentials['totp_secret']).now()
        result = session.post(base + '/login', data={
            'csrf': form.values['csrf'], 'username': credentials['username'],
            'password': credentials['password'], 'totp': code,
        }, allow_redirects=True, timeout=15)
        assert result.status_code == 200 and 'Perangkat' in result.text
        record('Admin password/TOTP login succeeds')

        now = datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()
        result = session.get(base + '/activity', params={'start': now, 'end': now,
                                                         'actor': credentials['username']}, timeout=15)
        assert result.status_code == 200 and 'Waktu WIB' in result.text
        assert 'Masuk dashboard' in result.text
        assert 'Aktivitas ditelusuri' in result.text
        record('Activity filter returns today in WIB and readable admin action')

        form = parse(result)
        assert form.values.get('csrf')
        result = session.post(base + '/activity/archives', data={
            'csrf': form.values['csrf'], 'start': now, 'end': now,
            'actor': credentials['username'], 'device': '', 'event': '',
        }, allow_redirects=True, timeout=15)
        assert result.status_code == 200 and 'Arsip aktivitas' in result.text
        links = re.findall(r'/activity/archives/([^/" ]+)/download', result.text)
        assert links
        archive_id = links[0]
        record('Filtered activity snapshot is retained in archive list')

        response = session.get(base + '/activity/archives/' + archive_id + '/download', timeout=15)
        assert response.status_code == 200
        payload = response.content
        digest = hashlib.sha256(payload).hexdigest()
        assert response.headers.get('X-Archive-SHA256') == digest
        with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
            manifest = json.loads(bundle.read('manifest.json'))
            rows = json.loads(bundle.read('aktivitas.json'))
            for name, expected in manifest['files_sha256'].items():
                assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            assert manifest['archive_id'] == archive_id and rows
            assert manifest['created_by'] == credentials['username']
            assert manifest['row_count'] == len(rows)
            assert_no_credentials(bundle, credentials)
            assert any(row['title'] == 'Masuk dashboard' for row in rows)
            assert any(row['title'] == 'Aktivitas ditelusuri' for row in rows)
        temp = archive_path.with_name('.' + archive_path.name + '.tmp')
        temp.write_bytes(payload)
        temp.chmod(0o600)
        temp.replace(archive_path)
        report.update(status='COMPLETE', archive_id=archive_id, row_count=len(rows),
                      sha256=digest, downloaded_archive=str(archive_path))
        record('Downloaded ZIP, contents, checksums and credential exclusion verified')
        print('PASS admin activity archive workflow; private evidence saved locally')
    except BaseException as exc:
        report['status'] = 'FAIL'
        report['error_type'] = type(exc).__name__
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
