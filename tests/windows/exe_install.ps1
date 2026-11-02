# Genuine EXE installer/wizard tests on an authorized disposable Windows VM.
# Device EXE must use an isolated schema1 fixture. Template uses the real roots.
param([Parameter(Mandatory=$true)][string]$TemplateExe,
      [Parameter(Mandatory=$true)][string]$DeviceExe,
      [Parameter(Mandatory=$true)][string]$Fixture,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$work=Split-Path -Parent $Report
$app=Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$data=Join-Path $env:ProgramFiles 'VanGuardEndpointData'
. (Join-Path $app 'Common.ps1')
Assert-Administrator;Assert-NoTunnel
if(Test-Path "$data\internet-lockdown"){throw 'Recover managed policy before maintenance'}
if((Get-Content -Raw "$Fixture\package\profile.json"|ConvertFrom-Json).schema -ne 1){throw 'Only schema1 fixture allowed'}
if((Get-PSDrive C).Free -lt 2GB){throw 'Insufficient test space'}
function Hashes([string[]]$Paths){
 $result=@{};foreach($path in $Paths){Get-ChildItem $path -Recurse -File -Force -ErrorAction Stop|ForEach-Object {$result[$_.FullName]=(Get-FileHash $_.FullName).Hash}};return $result
}
function Unchanged($Before){foreach($path in $Before.Keys){if((Get-FileHash $path).Hash -ne $Before[$path]){throw 'Preserved file changed'}}}
function Run([string]$Exe,[string]$Options,[string]$Name){
 $p=Start-Process $Exe -ArgumentList $Options -RedirectStandardOutput (Join-Path $work ($Name+'.stdout')) -RedirectStandardError (Join-Path $work ($Name+'.stderr')) -Wait -PassThru
 return $p.ExitCode
}
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
$backup=Join-Path $work 'before-exe-install'
if(Test-Path $backup){throw 'Preserve earlier backup'}
Protect-Directory $backup
foreach($item in @('config','identity','tools','setup-state.json')){Copy-Item -LiteralPath (Join-Path $data $item) -Destination $backup -Recurse}
Protect-Directory "$backup\app"
Get-ChildItem $app -File -Force|Copy-Item -Destination "$backup\app"
$primary=Hashes @("$data\config","$data\identity")
$fixtureFiles=Hashes @("$Fixture\data\config","$Fixture\data\identity","$Fixture\data\enrollment-request.json")
$old=Get-Content -Raw "$app\current.json"|ConvertFrom-Json
try {
 if((Run $DeviceExe '/prepare-only /nopause' 'device-first') -ne 20){throw 'Expected pending approval exit20'}
 if((Get-Content -Raw "$Fixture\data\wizard-state.json"|ConvertFrom-Json).phase -ne 'WAITING_APPROVAL'){throw 'Unexpected wizard phase'}
 Record 'device_exe_runs_real_wizard_and_forwards_exit20'
 $release=(Get-Content -Raw "$Fixture\app\current.json"|ConvertFrom-Json).release
 if((Run $DeviceExe '/prepare-only /nopause' 'device-resume') -ne 20 -or (Get-Content -Raw "$Fixture\app\current.json"|ConvertFrom-Json).release -ne $release){throw 'Device EXE resume failed'}
 Unchanged $fixtureFiles;Record 'device_resume_preserves_keys_config_request_and_runtime'
 if((Run $TemplateExe '/nopause' 'template-install') -ne 0){throw 'Template EXE installer failed'}
 Record 'template_exe_runs_real_offline_installer'
 $current=Get-Content -Raw "$app\current.json"|ConvertFrom-Json
 $state=Get-Content -Raw "$data\setup-state.json"|ConvertFrom-Json
 if($state.status -ne 'INSTALLED' -or $state.release -ne $current.release -or $current.release -eq $old.release){throw 'Incomplete new release'}
 $python=Join-Path $app ('releases\'+$current.release+'\venv\Scripts\python.exe')
 & $python -m pip check *> (Join-Path $work 'pip-check.log');if($LASTEXITCODE -ne 0){throw 'pip check failed'}
 & $python -m vanguard.client --help *> (Join-Path $work 'client-help.log');if($LASTEXITCODE -ne 0){throw 'Client entrypoint failed'}
 Record 'published_runtime_and_client_entrypoint_work'
 Unchanged $primary
 if(-not (Test-Path (Join-Path $app ('releases\'+$old.release)))){throw 'Old release removed'}
 Record 'primary_config_keys_and_old_release_preserved'
 Assert-NoTunnel
 if((Test-Path "$data\internet-lockdown") -or (Test-Path "$Fixture\data\internet-lockdown")){throw 'Unexpected managed policy'}
 Record 'no_tunnel_or_managed_policy_created'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {[pscustomobject]@{environment='Windows native; genuine EXEs, real installer; existing prerequisites';cases=$cases;backup=$backup;uac_fresh_os_login='BELUM_TERUJI'}|ConvertTo-Json -Depth 6|Set-Content $Report -Encoding UTF8}
