# Read-only installation verification after an interrupted test observer, plus
# device-wizard resume. Never infer success from a partial installer log alone.
param([Parameter(Mandatory=$true)][string]$BuildRoot,
      [Parameter(Mandatory=$true)][string]$Fixture,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$app=Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$data=Join-Path $env:ProgramFiles 'VanGuardEndpointData'
$backup=Join-Path $BuildRoot 'before-exe-install'
. (Join-Path $app 'Common.ps1')
Assert-Administrator;Assert-NoTunnel
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
function Snapshot([string[]]$Paths){$h=@{};foreach($path in $Paths){Get-ChildItem $path -Recurse -File -Force|ForEach-Object {$h[$_.FullName]=(Get-FileHash $_.FullName).Hash}};return $h}
function Same($Before){foreach($path in $Before.Keys){if((Get-FileHash $path).Hash -ne $Before[$path]){throw 'Preserved file changed'}}}
try {
 $log=[IO.File]::ReadAllText((Join-Path $BuildRoot 'template-install.stdout'))
 if($log.TrimEnd() -notmatch 'Exit code: 0$'){throw 'Template EXE completion not recorded'}
 $current=Get-Content -Raw "$app\current.json"|ConvertFrom-Json
 $state=Get-Content -Raw "$data\setup-state.json"|ConvertFrom-Json
 $old=Get-Content -Raw "$backup\app\current.json"|ConvertFrom-Json
 $manifest=Get-Content -Raw "$BuildRoot\template\manifest.json"|ConvertFrom-Json
 if($state.status -ne 'INSTALLED' -or $current.release -ne $state.release -or $current.release -eq $old.release -or $current.version -ne $manifest.version){throw 'Published installation inconsistent'}
 foreach($name in @('Common.ps1','VanGuard.ps1','VanGuard.bat','Internet-Lockdown.ps1')){if((Get-FileHash (Join-Path $app $name)).Hash.ToLowerInvariant() -ne $manifest.files.$name){throw 'Installed script differs from verified payload'}}
 Record 'template_exe_exit0_and_published_state_scripts_confirmed_after_boot'
 $python=Join-Path $app ('releases\'+$current.release+'\venv\Scripts\python.exe')
 & $python -m pip check *> "$BuildRoot\postflight-pip.log";if($LASTEXITCODE -ne 0){throw 'pip check failed'}
 & $python -m vanguard.client --help *> "$BuildRoot\postflight-help.log";if($LASTEXITCODE -ne 0){throw 'client entrypoint failed'}
 Record 'real_installed_dependencies_and_client_entrypoint_work'
 foreach($kind in @('config','identity')){
  $saved=Join-Path $backup $kind;$active=Join-Path $data $kind
  $before=@(Get-ChildItem $saved -Recurse -File -Force)
  if($before.Count -ne @(Get-ChildItem $active -Recurse -File -Force).Count){throw 'Primary file count differs'}
  foreach($f in $before){$relative=$f.FullName.Substring($saved.Length+1);if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash (Join-Path $active $relative)).Hash){throw 'Primary config/identity differs from backup'}}
 }
 if(-not (Test-Path (Join-Path $app ('releases\'+$old.release)))){throw 'Old release missing'}
 Record 'primary_config_keys_and_old_release_match_preinstall_backup'
 $preserved=Snapshot @("$Fixture\data\config","$Fixture\data\identity","$Fixture\data\enrollment-request.json","$Fixture\app\current.json")
 foreach($name in @('first','resume')){
  $p=Start-Process "$BuildRoot\DeviceFixture.exe" -ArgumentList '/prepare-only /nopause' -RedirectStandardOutput "$BuildRoot\postflight-device-$name.stdout" -RedirectStandardError "$BuildRoot\postflight-device-$name.stderr" -Wait -PassThru
  if($p.ExitCode -ne 20 -or (Get-Content -Raw "$Fixture\data\wizard-state.json"|ConvertFrom-Json).phase -ne 'WAITING_APPROVAL'){throw 'Device wizard did not return pending approval'}
  Same $preserved
  Record ('device_exe_'+$name+'_exit20_preserves_keys_config_request_runtime')
 }
 Assert-NoTunnel
 if((Test-Path "$data\internet-lockdown") -or (Test-Path "$Fixture\data\internet-lockdown")){throw 'Unexpected managed policy'}
 Record 'no_tunnel_or_managed_policy_created'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {[pscustomobject]@{environment='Windows native after guest shutdown; original installation log plus independent state verification; real device EXE resume';cases=$cases}|ConvertTo-Json -Depth 6|Set-Content $Report -Encoding UTF8}
