# Actual offline runtime repair in isolated application/data roots. No service,
# firewall, CA issuance or login. Existing Python/WireGuard must already exist.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
. (Join-Path $Package 'Common.ps1')
Assert-Administrator
Assert-NoTunnel
$originalApp=$AppRoot;$originalData=$DataRoot
if(-not (Test-Path "$env:ProgramFiles\Python313\python.exe") -or -not (Test-Path "$env:ProgramFiles\WireGuard\wireguard.exe")){throw 'This test requires existing runtimes; use the fresh OS matrix separately'}
if((Get-Content -Raw (Join-Path $Package 'profile.json')|ConvertFrom-Json).schema -ne 1){throw 'Only schema1 allowed in this isolated repair test'}
# Keep the fixture path as short as the product root on Windows without long paths.
$work=Join-Path $env:ProgramFiles ('VGRT-'+[guid]::NewGuid().ToString('N').Substring(0,8))
if(Test-Path $work){throw 'Preserve an existing fixture'}
Protect-Directory $work
$source=Join-Path $work 'package'
Copy-Item -LiteralPath $Package -Destination $source -Recurse
$fixtureApp=Join-Path $work 'app';$fixtureData=Join-Path $work 'data'
$common=Get-Content -Raw (Join-Path $source 'Common.ps1')
$appLine='$AppRoot = Join-Path $env:ProgramFiles ''VanGuardEndpoint'''
$dataLine='$DataRoot = Join-Path $env:ProgramFiles ''VanGuardEndpointData'''
if(-not $common.Contains($appLine) -or -not $common.Contains($dataLine)){throw 'Fixture root override not understood'}
$common=$common.Replace($appLine,('$AppRoot = '''+$fixtureApp+'''')).Replace($dataLine,('$DataRoot = '''+$fixtureData+''''))
[IO.File]::WriteAllText((Join-Path $source 'Common.ps1'),$common)
$manifest=Get-Content -Raw (Join-Path $source 'manifest.json')|ConvertFrom-Json
$manifest.files.'Common.ps1'=(Get-FileHash (Join-Path $source 'Common.ps1')).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $source 'manifest.json'),($manifest|ConvertTo-Json -Depth 8))
function Hash-Files([string[]]$Paths){
    $result=@{}
    foreach($path in $Paths){if(Test-Path $path){Get-ChildItem $path -Recurse -File -Force|ForEach-Object {$result[$_.FullName]=(Get-FileHash $_.FullName).Hash}}}
    return $result
}
function Assert-Hashes($Before){foreach($path in $Before.Keys){if((Get-FileHash $path).Hash -ne $Before[$path]){throw 'Preserved file changed'}}}
$original=Hash-Files @("$originalData\config","$originalData\identity","$originalApp\current.json","$originalData\setup-state.json")
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
function Run-Setup([string]$Name){
    $p=Start-Process cmd.exe -ArgumentList ('/c ""'+$source+'\Setup-VanGuard.bat" /prepare-only /nopause"') -RedirectStandardOutput (Join-Path $work ($Name+'.stdout')) -RedirectStandardError (Join-Path $work ($Name+'.stderr')) -Wait -PassThru
    if($p.ExitCode -ne 20 -or (Get-Content -Raw "$fixtureData\wizard-state.json"|ConvertFrom-Json).phase -ne 'WAITING_APPROVAL'){throw 'Expected pending approval after actual runtime setup'}
}
try {
    Run-Setup 'initial';Record 'actual_runtime_install_pending_approval'
    $first=Get-Content -Raw "$fixtureApp\current.json"|ConvertFrom-Json
    $preserved=Hash-Files @("$fixtureData\identity","$fixtureData\config","$fixtureData\enrollment-request.json")
    Copy-Item "$fixtureData\setup-state.json" (Join-Path $work 'setup-state-before.json')
    # Inject the precise on-disk boundary: old current remains while a new release
    # is IN_PROGRESS. This is controlled state injection, not a physical crash.
    $partial=$first.release.Substring(0,64)+'-'+[guid]::NewGuid().ToString('N')
    Protect-Directory (Join-Path $fixtureApp ('releases\'+$partial))
    Write-State "$fixtureData\setup-state.json" @{schema=1;status='IN_PROGRESS';phase='install-runtime';release=$partial}
    Run-Setup 'repair';Record 'same_package_repairs_interrupted_runtime'
    $current=Get-Content -Raw "$fixtureApp\current.json"|ConvertFrom-Json
    $setup=Get-Content -Raw "$fixtureData\setup-state.json"|ConvertFrom-Json
    if($current.release -eq $first.release -or $current.release -eq $partial -or $setup.release -ne $current.release -or $setup.status -ne 'INSTALLED'){throw 'Repair did not publish a new complete release'}
    Record 'new_complete_runtime_published'
    if(-not (Test-Path (Join-Path $fixtureApp ('releases\'+$first.release))) -or -not (Test-Path (Join-Path $fixtureApp ('releases\'+$partial)))){throw 'Earlier release evidence removed'}
    Assert-Hashes $preserved;Record 'keys_config_request_and_prior_releases_preserved'
    Run-Setup 'resume'
    if((Get-Content -Raw "$fixtureApp\current.json"|ConvertFrom-Json).release -ne $current.release){throw 'Complete resume reinstalled unnecessarily'}
    Record 'complete_resume_reuses_runtime'
    & sc.exe query 'WireGuardTunnel$vanguard-client' *> $null
    if($LASTEXITCODE -ne 1060 -or (Test-Path "$fixtureData\internet-lockdown")){throw 'Unexpected tunnel/policy'}
    Record 'no_tunnel_or_managed_policy'
    Assert-Hashes $original;Record 'existing_endpoint_state_preserved'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {[pscustomobject]@{environment='Windows native; real offline installer and venv; isolated roots';cases=$cases;test_path=$work;interruption='controlled state injection';fresh_os_uac='BELUM_TERUJI'}|ConvertTo-Json -Depth 6|Set-Content $Report -Encoding UTF8}
