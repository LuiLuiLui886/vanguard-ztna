import io
import zipfile

import pytest

from scripts.verify_activity_archive import assert_no_credentials


@pytest.mark.parametrize('field', ['password', 'totp_secret'])
def test_compressed_member_secret_is_rejected(field):
    credentials = {'password': 'synthetic-password-for-archive-test',
                   'totp_secret': 'SYNTHETICSEEDFORARCHIVETEST'}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', '{}')
        archive.writestr('future-format.txt', credentials[field])
    payload = stream.getvalue()
    assert credentials[field].encode() not in payload
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        with pytest.raises(AssertionError):
            assert_no_credentials(archive, credentials)


def test_clean_members_are_accepted():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', '{}')
        archive.writestr('aktivitas.csv', 'Waktu WIB,Aktivitas\n')
    with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
        assert_no_credentials(archive, {'password': 'synthetic-password',
                                        'totp_secret': 'SYNTHETICSEED'})
