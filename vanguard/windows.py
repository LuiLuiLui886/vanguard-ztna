"""Native Windows client helpers; WireGuard itself remains unmodified."""

import ctypes
import os
import stat
import subprocess
from pathlib import Path

from .common import Rejected, run


def require_administrator():
    if os.name != 'nt' or not ctypes.windll.shell32.IsUserAnAdmin():
        raise Rejected('Run VanGuard from an elevated Windows terminal')


def check_private_path(path):
    require_administrator()
    absolute = Path(os.path.abspath(path))
    for part in (absolute, *absolute.parents):
        try:
            attrs = part.lstat().st_file_attributes
        except FileNotFoundError:
            continue
        if attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Rejected('Identity path must not traverse a reparse point')


def protect_directory(path):
    """Private keys inherit an explicit protected DACL for SYSTEM/Admins only."""
    require_administrator()
    import ntsecuritycon
    import win32security

    path = Path(path)
    if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise Rejected('Identity directory must not be a reparse point')
    acl = win32security.ACL()
    inherit = win32security.OBJECT_INHERIT_ACE | win32security.CONTAINER_INHERIT_ACE
    for sid in ('S-1-5-18', 'S-1-5-32-544'):
        acl.AddAccessAllowedAceEx(win32security.ACL_REVISION_DS, inherit,
                                 ntsecuritycon.FILE_ALL_ACCESS,
                                 win32security.ConvertStringSidToSid(sid))
    win32security.SetNamedSecurityInfo(
        str(path), win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
        None, None, acl, None,
    )


class WindowsTunnel:
    name = 'vanguard-client'

    def __init__(self):
        self.executable = str(Path(os.environ.get('ProgramFiles', r'C:\Program Files'))
                              / 'WireGuard' / 'wireguard.exe')

    def preflight(self):
        require_administrator()
        if not Path(self.executable).is_file():
            raise Rejected('Install the official WireGuard for Windows client first')
        result = subprocess.run(['sc.exe', 'query', 'WireGuardTunnel$' + self.name],
                                capture_output=True, timeout=15)
        # 1060 is ERROR_SERVICE_DOES_NOT_EXIST, independent of Windows UI language.
        if result.returncode != 1060:
            raise Rejected('Tunnel service exists or cannot be inspected; stop and inspect it first')

    def up(self, config):
        run([self.executable, '/installtunnelservice', str(config)])
        # Boot must not reconnect from a stored config without a new client process.
        run(['sc.exe', 'config', 'WireGuardTunnel$' + self.name, 'start=', 'demand'])

    def down(self, config):
        run([self.executable, '/uninstalltunnelservice', self.name])
