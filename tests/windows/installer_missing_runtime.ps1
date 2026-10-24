# Run only on a disposable Windows disk with both shared runtimes already absent.
# This test never removes an existing runtime to obtain its precondition.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$ExpectedManifestSha256,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$results=New-Object System.Collections.Generic.List[object]
$python=Join-Path $env:ProgramFiles 'Python313\python.exe'
$wg=Join-Path $env:ProgramFiles 'WireGuard\wireguard.exe'
$app=Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$data=Join-Path $env:ProgramFiles 'VanGuardEndpointData'
try {
    if ((Test-Path $python) -or (Test-Path $wg) -or (Test-Path $app) -or (Test-Path $data)) { throw 'Test requires absent runtimes and endpoint; preserve existing installations.' }
    if ((Get-FileHash (Join-Path $Package 'manifest.json')).Hash -ne $ExpectedManifestSha256) { throw 'Untrusted test package' }
    $results.Add(@{case='runtimes_and_endpoint_absent_before';status='PASS'})
    & (Join-Path $Package 'Install-VanGuard.bat') /nopause
    if ($LASTEXITCODE -ne 0) { throw "Installer exit $LASTEXITCODE" }
    $results.Add(@{case='bat_installs_missing_runtimes_and_endpoint';status='PASS'})
    $version=& $python -c "import sys; print('.'.join(map(str,sys.version_info[:3])))"
    $lock=Get-Content -Raw (Join-Path $Package 'runtime-lock.json') | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $version -ne $lock.python.version -or (Get-Item $wg).VersionInfo.ProductVersion -ne $lock.wireguard.version) { throw 'Unexpected installed runtime versions' }
    $results.Add(@{case='installed_runtime_versions_match_lock';status='PASS';python=$version;wireguard=$lock.wireguard.version})
    $current=Get-Content -Raw (Join-Path $app 'current.json') | ConvertFrom-Json
    $runtime=Join-Path $app ('releases\'+$current.release+'\venv\Scripts\python.exe')
    & $runtime -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Installed dependency check failed' }
    & (Join-Path $app 'VanGuard.bat') status /nopause
    if ($LASTEXITCODE -ne 0) { throw 'Status failed after fresh runtime install' }
    $results.Add(@{case='installed_dependencies_and_status';status='PASS'})
    if ((Test-Path (Join-Path $data 'identity')) -or @(Get-Service -Name 'WireGuardTunnel$*' -ErrorAction SilentlyContinue).Count) { throw 'Unexpected identity or tunnel' }
    $results.Add(@{case='no_identity_or_tunnel_created';status='PASS'})
} catch {
    $results.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message})
    throw
} finally {
    [pscustomobject]@{schema=1;environment='Windows VM disposable disk, native runtime installers';cases=$results;
      uac_interactive='BELUM_TERUJI';physical_endpoint='BELUM_TERUJI'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Report -Encoding UTF8
}
