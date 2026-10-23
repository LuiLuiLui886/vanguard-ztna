# Run only on the backed-up Windows test VM, elevated, after verifying the kit ZIP.
# Fresh endpoint install must not exist; original ProgramData VM identity is untouched.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$ExpectedManifestSha256,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$data = Join-Path $env:ProgramFiles 'VanGuardEndpointData'
$results = New-Object System.Collections.Generic.List[object]
function Record([string]$Name) { $results.Add(@{case=$Name;status='PASS'}) }
function Run-Bat {
    & "$env:SystemRoot\System32\cmd.exe" /d /c ('""' + (Join-Path $Package 'Install-VanGuard.bat') + '" /nopause"')
    if ($LASTEXITCODE -ne 0) { throw "BAT failed: $LASTEXITCODE" }
}
try {
    if ((Test-Path -LiteralPath $root) -or (Test-Path -LiteralPath $data)) { throw 'Fresh endpoint test requires absent app/data directories; never remove existing identity to run this test.' }
    if ((Get-FileHash (Join-Path $Package 'manifest.json')).Hash -ne $ExpectedManifestSha256) { throw 'Untrusted test package.' }
    & powershell.exe -NoProfile -File (Join-Path $Package 'Install-VanGuard.ps1') -Preview
    if ($LASTEXITCODE -ne 0 -or (Test-Path -LiteralPath $root) -or (Test-Path -LiteralPath $data)) { throw 'Preview changed state or failed.' }
    Record 'preview_no_application_state'
    Run-Bat
    Record 'bat_fresh_endpoint_install'
    & powershell.exe -NoProfile -File (Join-Path $root 'VanGuard.ps1') -Action status
    if ($LASTEXITCODE -ne 0) { throw 'Fresh status failed.' }
    Record 'status_needs_profile'
    if (Test-Path -LiteralPath (Join-Path $data 'identity')) { throw 'Installer created identity.' }
    & sc.exe query 'WireGuardTunnel$vanguard-client' *> $null
    if ($LASTEXITCODE -ne 1060) { throw 'Unexpected tunnel/service inspection failure.' }
    Record 'no_identity_or_tunnel_created'
    $sentinel = Join-Path $data 'config\preservation-test.txt'
    [IO.File]::WriteAllText($sentinel,'non-secret disposable marker')
    $hash = (Get-FileHash -LiteralPath $sentinel).Hash
    $first = (Get-Content -Raw (Join-Path $root 'current.json') | ConvertFrom-Json).release
    Run-Bat
    $second = (Get-Content -Raw (Join-Path $root 'current.json') | ConvertFrom-Json).release
    if ($first -eq $second -or (Get-FileHash $sentinel).Hash -ne $hash) { throw 'Reinstall did not preserve config/use fresh runtime.' }
    Record 'reinstall_preserves_config'
    $setupPath = Join-Path $data 'setup-state.json'
    $original = [IO.File]::ReadAllBytes($setupPath)
    try {
        $state = Get-Content -Raw $setupPath | ConvertFrom-Json
        $state.status = 'IN_PROGRESS'
        [IO.File]::WriteAllText($setupPath,($state | ConvertTo-Json))
        & powershell.exe -NoProfile -File (Join-Path $root 'VanGuard.ps1') -Action status
        if ($LASTEXITCODE -eq 0) { throw 'Incomplete setup incorrectly reported success.' }
        Record 'incomplete_setup_blocks_launcher'
    } finally { [IO.File]::WriteAllBytes($setupPath,$original) }
    Run-Bat
    if ((Get-FileHash $sentinel).Hash -ne $hash) { throw 'Repair altered data.' }
    Record 'repair_preserves_config'
    & powershell.exe -NoProfile -File (Join-Path $root 'Uninstall-VanGuard.ps1')
    if ($LASTEXITCODE -ne 0 -or (Test-Path $root) -or (Get-FileHash $sentinel).Hash -ne $hash) { throw 'Uninstall failed or removed preserved data.' }
    if (-not (Test-Path "$env:ProgramFiles\WireGuard\wireguard.exe")) { throw 'Shared WireGuard removed.' }
    Record 'uninstall_preserves_data_and_shared_runtime'
    Run-Bat
    Record 'reinstall_after_uninstall'
} catch {
    $results.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message})
    throw
} finally {
    [pscustomobject]@{schema=1;environment='Windows VM native';cases=$results;
        uac_interactive='BELUM_DIJALANKAN';missing_runtime_install='BELUM_DIJALANKAN';
        physical_endpoint='BELUM_DIJALANKAN'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Report -Encoding UTF8
}
