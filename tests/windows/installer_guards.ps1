# Native regression tests; no installation, service creation or credential use.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
. (Join-Path $Package 'Common.ps1')
. (Join-Path $Package 'Runtime.ps1')
$results=New-Object System.Collections.Generic.List[object]
$testRoot=Join-Path $env:ProgramFiles ('VanGuardGuardTest-'+[guid]::NewGuid().ToString('N'))
function Check([string]$Name,[scriptblock]$Body) {
    & $Body
    $results.Add(@{case=$Name;status='PASS'})
}
function Must-Reject([scriptblock]$Body) {
    $rejected=$false
    try { & $Body } catch { $rejected=$true }
    if (-not $rejected) { throw 'Expected rejection did not occur.' }
}
try {
    Protect-Directory $testRoot
    Check 'native_program_files_sid_acl' { Assert-SafePath $Package }
    $unsafe=Join-Path $testRoot 'writable'
    Protect-Directory $unsafe
    $acl=Get-Acl -LiteralPath $unsafe
    $rule=New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')),'Modify','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule); Set-Acl -LiteralPath $unsafe -AclObject $acl
    Check 'reject_users_writable_path' { Must-Reject { Assert-SafePath $unsafe } }
    $link=Join-Path $testRoot 'junction'
    New-Item -ItemType Junction -Path $link -Target $Package | Out-Null
    Check 'reject_junction' { Must-Reject { Assert-SafePath $link } }
    $pythonInstaller=Join-Path $Package 'runtimes\python-3.13.17-amd64.exe'
    Check 'reject_valid_signature_wrong_publisher' { Must-Reject { Assert-Publisher $pythonInstaller 'WireGuard LLC' } }
    $runtimeDir=Join-Path $testRoot 'runtimes'
    Protect-Directory $runtimeDir
    $lock=Get-Content -Raw (Join-Path $Package 'runtime-lock.json') | ConvertFrom-Json
    # Deliberately corrupt bytes: failure must occur before any process installer.
    [IO.File]::WriteAllText((Join-Path $testRoot $lock.python.file),'invalid-runtime')
    [IO.File]::WriteAllText((Join-Path $testRoot $lock.wireguard.file),'invalid-runtime')
    Copy-Item -LiteralPath (Join-Path $Package 'runtime-lock.json') -Destination $testRoot
    Check 'reject_tampered_runtime_before_execution' { Must-Reject { Ensure-Runtimes $testRoot } }
} catch {
    $results.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message}); throw
} finally {
    # Keep disposable test evidence. Never recurse-delete a junction.
    [pscustomobject]@{schema=1;environment='Windows native';cases=$results;test_path=$testRoot} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Report -Encoding UTF8
}
