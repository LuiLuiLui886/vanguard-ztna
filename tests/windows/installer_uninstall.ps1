# Continue after the smoke test; preserve its data and test the actual uninstall BAT.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$data=Join-Path $env:ProgramFiles 'VanGuardEndpointData'
$sentinel=Join-Path $data 'config\preservation-test.txt'
$hash=(Get-FileHash -LiteralPath $sentinel).Hash
$results=New-Object System.Collections.Generic.List[object]
try {
    if (Test-Path -LiteralPath $root) { throw 'Expected previous uninstall removed AppRoot. Do not erase a live installation.' }
    & (Join-Path $Package 'Install-VanGuard.bat') /nopause
    if ($LASTEXITCODE -ne 0 -or (Get-FileHash $sentinel).Hash -ne $hash) { throw 'Reinstall failed or altered data.' }
    $results.Add(@{case='reinstall_preserved_data';status='PASS'})
    & (Join-Path $root 'Uninstall-VanGuard.bat') /nopause
    if ($LASTEXITCODE -ne 0 -or (Test-Path -LiteralPath $root) -or (Get-FileHash $sentinel).Hash -ne $hash) { throw 'Uninstall exit/state/preservation failed.' }
    if (-not (Test-Path "$env:ProgramFiles\WireGuard\wireguard.exe")) { throw 'Shared WireGuard removed.' }
    $results.Add(@{case='uninstall_exit_and_preservation';status='PASS'})
    & (Join-Path $Package 'Install-VanGuard.bat') /nopause
    if ($LASTEXITCODE -ne 0 -or (Get-FileHash $sentinel).Hash -ne $hash) { throw 'Final reinstall failed.' }
    & (Join-Path $root 'VanGuard.bat') status /nopause
    if ($LASTEXITCODE -ne 0) { throw 'Final launcher status failed.' }
    $results.Add(@{case='reinstall_after_corrected_uninstall';status='PASS'})
} catch { $results.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message}); throw }
finally {
    [pscustomobject]@{schema=1;environment='Windows VM native';cases=$results} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Report -Encoding UTF8
}
