# Read-only endpoint preparation check. Run from an independently verified kit.
param(
    [Parameter(Mandatory=$true)][ValidateSet('PC','Laptop')][string]$Role,
    [string]$PythonPath = (Join-Path $env:ProgramFiles 'Python313\python.exe')
)
$ErrorActionPreference = 'Stop'
$kit = Split-Path -Parent $PSScriptRoot
. (Join-Path $kit 'windows\Common.ps1')
$checks = New-Object System.Collections.Generic.List[object]
function Add-Check([string]$Name,[string]$Status,[string]$Reason) {
    $checks.Add([pscustomobject]@{check=$Name;status=$Status;reason=$Reason})
}
try {
    Assert-Administrator
    Assert-SafePath $kit
    Add-Check 'privilege_and_kit_path' 'PASS' 'Elevated; protected path checked. Verify kit digest independently before execution.'
} catch {
    Add-Check 'privilege_and_kit_path' 'FAIL' 'Use an administrator terminal and independently verified kit in an admin-only path.'
    $checks | ConvertTo-Json -Depth 5
    exit 2
}
try {
    $os = Get-CimInstance Win32_OperatingSystem
    if ([int]$os.BuildNumber -ge 22000 -and $os.ProductType -eq 1 -and $env:PROCESSOR_ARCHITECTURE -eq 'AMD64') {
        Add-Check 'windows_target' 'PASS' 'Windows build and x64 match candidate target; native lifecycle still needs testing.'
    } else { Add-Check 'windows_target' 'FAIL' 'Candidate requires Windows 11 x64.' }
} catch { Add-Check 'windows_target' 'UNKNOWN' 'OS inspection failed.' }
$expected = if ($Role -eq 'PC') { '192.168.50.20' } else { '192.168.50.30' }
try {
    $addresses = @(Get-NetIPAddress -AddressFamily IPv4)
    $match = @($addresses | Where-Object { $_.IPAddress -eq $expected -and $_.PrefixLength -eq 24 })
    if ($match.Count -ne 1) { Add-Check 'endpoint_address' 'FAIL' 'Expected approved endpoint address /24 on one interface.' }
    else {
        $adapter = Get-NetAdapter | Where-Object { $_.ifIndex -eq $match[0].InterfaceIndex }
        if ($adapter.Status -eq 'Up') { Add-Check 'endpoint_address' 'PASS' 'Approved address on an Up adapter; verify LAN/SSID manually.' }
        else { Add-Check 'endpoint_address' 'FAIL' 'Expected adapter is not Up.' }
        $routes = @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '192.168.100.20/32' -ErrorAction SilentlyContinue |
                    Where-Object { $_.NextHop -eq '192.168.50.10' -and $_.InterfaceIndex -eq $match[0].InterfaceIndex })
        if ($routes.Count -gt 0) { Add-Check 'server_host_route' 'PASS' 'Approved /32 route exists; this does not prove host forwarding.' }
        else { Add-Check 'server_host_route' 'FAIL' 'Required /32 route via 192.168.50.10 is absent.' }
    }
} catch { Add-Check 'endpoint_network' 'UNKNOWN' 'Network inspection failed.' }
try {
    Assert-SafePath $PythonPath
    & $PythonPath -c "import sys,struct,ssl,venv,ensurepip; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8"
    if ($LASTEXITCODE -ne 0) { throw 'runtime' }
    Add-Check 'python_runtime' 'PASS' 'Python3.13 x64 with SSL/venv/ensurepip; runtime origin must be verified by operator.'
} catch { Add-Check 'python_runtime' 'FAIL' 'Install verified Python3.13 x64 for all users, including pip/venv; specify its protected path.' }
try {
    $wireguard = Join-Path $env:ProgramFiles 'WireGuard\wireguard.exe'
    Assert-SafePath $wireguard
    $signature = Get-AuthenticodeSignature -LiteralPath $wireguard
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'WireGuard') { throw 'signature' }
    Add-Check 'wireguard_signature' 'PASS' 'Valid signature; installer still requires independently confirmed signer thumbprint.'
    Assert-NoTunnel
    Add-Check 'existing_tunnel' 'PASS' 'No VanGuard tunnel service/ownership marker detected.'
} catch { Add-Check 'wireguard_or_tunnel' 'UNKNOWN' 'WireGuard signature/path or tunnel ownership needs inspection. Do not delete config.' }
Add-Check 'trust_tls_udp_application' 'NOT_TESTED' 'Confirm root/key separately; run launcher diagnose after install, then admission/handshake/application tests.'
Add-Check 'native_installer_lifecycle' 'NOT_TESTED' 'Fresh/reinstall/repair/upgrade/uninstall/ACL/UAC remain required.'
$status = if (@($checks | Where-Object { $_.status -in @('FAIL','UNKNOWN') }).Count) { 'BLOCKED' } else { 'MANUAL_REVIEW_REQUIRED' }
[pscustomobject]@{schema=1;role=$Role;observed_at=[DateTime]::UtcNow.ToString('o');status=$status;ready_for_production=$false;mutations=$false;checks=$checks} | ConvertTo-Json -Depth 5
exit 2
