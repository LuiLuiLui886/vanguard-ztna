# Runs once, elevated, from the private installation seed in the new Windows VM.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:ProgramData 'VanGuard'
New-Item -ItemType Directory -Force $root | Out-Null
& icacls.exe $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Cannot protect setup directory' }
$report = @{ status = 'IN_PROGRESS'; phase = 'network'; updated_at = (Get-Date).ToUniversalTime().ToString('o') }
function Save-Report {
    $report.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $report | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $root 'windows-setup.json')
}
Save-Report
try {
    $nic = @(Get-NetAdapter | Where-Object { $_.MacAddress -eq '52-54-00-76-00-3C' })
    if ($nic.Count -ne 1) { throw 'Expected the Windows lab network adapter' }
    $index = $nic[0].ifIndex
    Set-NetIPInterface -InterfaceIndex $index -AddressFamily IPv4 -Dhcp Disabled
    if (-not (Get-NetIPAddress -InterfaceIndex $index -IPAddress '192.168.100.60' -ErrorAction SilentlyContinue)) {
        New-NetIPAddress -InterfaceIndex $index -IPAddress '192.168.100.60' -PrefixLength 24 -DefaultGateway '192.168.100.1' | Out-Null
    }
    Set-DnsClientServerAddress -InterfaceIndex $index -ServerAddresses '192.168.100.1'
    Set-TimeZone -Id 'SE Asia Standard Time'
    Set-Service w32time -StartupType Automatic
    Start-Service w32time
    & w32tm.exe /resync | Out-Null

    $report.phase = 'openssh'
    Save-Report
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
    Stop-Service sshd -ErrorAction SilentlyContinue
    # Restrict the inbox rule before starting the service.
    $rule = Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue
    if ($rule) {
        $rule | Set-NetFirewallRule -RemoteAddress '192.168.100.1' -Profile Any
    } else {
        New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'VanGuard host SSH' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -RemoteAddress '192.168.100.1' -Profile Any | Out-Null
    }
    $ssh = Join-Path $env:ProgramData 'ssh'
    New-Item -ItemType Directory -Force $ssh | Out-Null
    Copy-Item (Join-Path $PSScriptRoot 'host-access.pub') (Join-Path $ssh 'administrators_authorized_keys')
    & icacls.exe (Join-Path $ssh 'administrators_authorized_keys') /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Cannot protect SSH authorization file' }
    @'
Port 22
ListenAddress 192.168.100.60
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
Subsystem sftp sftp-server.exe
'@ | Set-Content -Encoding ASCII (Join-Path $ssh 'sshd_config')
    Set-Service sshd -StartupType Automatic
    Start-Service sshd
    $report.status = 'WINDOWS_SETUP_COMPLETE'
    $report.phase = 'awaiting_client_installation_and_admission'
    $report.os = (Get-CimInstance Win32_OperatingSystem).Caption
    $report.build = (Get-CimInstance Win32_OperatingSystem).BuildNumber
    $report.secure_boot = Confirm-SecureBootUEFI
    $report.tpm_present = (Get-Tpm).TpmPresent
    $report.address = '192.168.100.60'
    Save-Report
} catch {
    $report.status = 'FAILED'
    # Phase is enough to resume; do not serialize exceptions that could contain data.
    Save-Report
    throw
} finally {
    $logon = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
    Set-ItemProperty $logon AutoAdminLogon '0'
    Remove-ItemProperty $logon DefaultPassword -ErrorAction SilentlyContinue
    Remove-ItemProperty $logon AutoLogonCount -ErrorAction SilentlyContinue
    foreach ($path in @('C:\Windows\Panther\unattend.xml', 'C:\Windows\Panther\Unattend\unattend.xml', 'C:\Windows\System32\Sysprep\unattend.xml')) {
        if (Test-Path $path) { Remove-Item $path -Force }
    }
}
