# Native setup/resume probe for an explicitly backed-up disposable endpoint.
param([switch]$AllowPreparedEndpointMutation,[switch]$ExpectApproved,
      [Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
if(-not $AllowPreparedEndpointMutation){throw 'Prepare backups, disposable config/identity, and console recovery first.'}
$directory='C:\Program Files\VanGuardEndpointData'
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
function Identity-Hashes {
    $result=@{}
    foreach($name in @('identity.key','wg.key','request.json')){
        $result[$name]=(Get-FileHash (Join-Path $directory ('identity\'+$name))).Hash
    }
    return $result
}
try {
    $expected=if($ExpectApproved){0}else{20}
    for($attempt=1;$attempt -le 2;$attempt++){
        $p=Start-Process cmd.exe -ArgumentList ('/c ""'+$Package+'\Setup-VanGuard.bat" /prepare-only /nopause"') -RedirectStandardOutput ($Report+".$attempt.stdout") -RedirectStandardError ($Report+".$attempt.stderr") -Wait -PassThru
        if($p.ExitCode -ne $expected){throw ('Unexpected setup exit: '+$p.ExitCode)}
        Record ('setup_expected_exit_attempt_'+$attempt)
        $phase=(Get-Content -Raw "$directory\wizard-state.json"|ConvertFrom-Json).phase
        if(($ExpectApproved -and $phase -ne 'READY_FOR_LOGIN') -or (-not $ExpectApproved -and $phase -ne 'WAITING_APPROVAL')){throw 'Phase differs from actual enrollment'}
        Record ('phase_matches_enrollment_attempt_'+$attempt)
        & sc.exe query 'WireGuardTunnel$vanguard-client' *> $null
        if($LASTEXITCODE -ne 1060){throw 'Setup unexpectedly created tunnel or service inspection failed'}
        Record ('no_tunnel_before_login_attempt_'+$attempt)
        $request=Get-Content -Raw "$directory\enrollment-request.json"|ConvertFrom-Json
        if((($request.PSObject.Properties.Name|Sort-Object) -join ',') -ne 'csr,device_id,tunnel_ip,wg_public_key'){throw 'Unexpected exported fields'}
        Record ('public_only_export_attempt_'+$attempt)
        $current=(Get-Content -Raw 'C:\Program Files\VanGuardEndpoint\current.json'|ConvertFrom-Json).release
        if($attempt -eq 1){$before=Identity-Hashes;$release=$current}
        else{
            $after=Identity-Hashes
            foreach($name in $before.Keys){if($before[$name] -ne $after[$name]){throw 'Resume changed identity'}}
            if($current -ne $release){throw 'Resume unnecessarily reinstalled runtime'}
            Record 'resume_preserves_keys_and_runtime'
        }
    }
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {[pscustomobject]@{environment='Windows native; prepared disposable endpoint';cases=$cases;interactive_login_uac='BELUM_TERUJI'}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $Report -Encoding UTF8}
