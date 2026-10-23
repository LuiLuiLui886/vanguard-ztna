# Test BAT policy handling in a disposable process, never writing registry policies.
param([Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Continue'
$launcher=Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
$original=$env:PSExecutionPolicyPreference
$persistent=Get-ExecutionPolicy -List | Where-Object Scope -ne Process | ConvertTo-Json
try {
    if (@(Get-ExecutionPolicy -List | Where-Object { $_.Scope -ne 'Process' -and $_.ExecutionPolicy -ne 'Undefined' }).Count) { throw 'This default-policy regression requires unconfigured persistent policies.' }
    Remove-Item Env:\PSExecutionPolicyPreference -ErrorAction SilentlyContinue
    & $launcher status /nopause
    $defaultExit=$LASTEXITCODE
    $env:PSExecutionPolicyPreference='Restricted'
    & $launcher status /nopause
    $restrictedExit=$LASTEXITCODE
    $after=Get-ExecutionPolicy -List | Where-Object Scope -ne Process | ConvertTo-Json
    if ($defaultExit -ne 0 -or $restrictedExit -eq 0 -or $persistent -ne $after) { throw 'BAT policy regression failed.' }
    [pscustomobject]@{schema=1;default_exit=$defaultExit;restricted_exit=$restrictedExit;persistent_unchanged=($persistent -eq $after);status='PASS'} |
        ConvertTo-Json | Set-Content -LiteralPath $Report -Encoding UTF8
} finally {
    if ($null -eq $original) { Remove-Item Env:\PSExecutionPolicyPreference -ErrorAction SilentlyContinue }
    else { $env:PSExecutionPolicyPreference=$original }
}
