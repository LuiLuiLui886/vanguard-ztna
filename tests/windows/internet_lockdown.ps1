# Destructive network test ONLY on an explicitly prepared disposable Windows VM.
param([switch]$AllowFirewallMutation,[switch]$ExistingPolicy,[Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
if(-not $AllowFirewallMutation){throw 'Run only on backed-up test VM with local console recovery.'}
$base=Split-Path -Parent $Report
$script='C:\Program Files\VanGuardEndpoint\Internet-Lockdown.ps1'
$profile=Get-Content -Raw 'C:\Program Files\VanGuardEndpointData\config\profile.json'|ConvertFrom-Json
$api=[Uri]$profile.api_url
function Probe([string]$HostName,[int]$Port) {
    $client=New-Object Net.Sockets.TcpClient
    try {$pending=$client.BeginConnect($HostName,$Port,$null,$null);if(-not $pending.AsyncWaitHandle.WaitOne(3000)){return $false};$client.EndConnect($pending);return $true}
    catch{return $false}finally{$client.Dispose()}
}
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
function Action([string]$Name) {
    $p=Start-Process powershell.exe -ArgumentList ('-NoProfile -ExecutionPolicy RemoteSigned -File "'+$script+'" -Action '+$Name) -RedirectStandardOutput "$base\$Name.stdout" -RedirectStandardError "$base\$Name.stderr" -Wait -PassThru
    if($p.ExitCode -ne 0){throw ('Policy '+$Name+' exit '+$p.ExitCode)}
}
try {
    if(-not $ExistingPolicy) {
        if(-not (Probe '1.1.1.1' 443)){throw 'Internet baseline unavailable; cannot prove blocking'}
        Record 'internet_reachable_before_lockdown'
        Action 'preview';Record 'preview_pass'
        Action 'enable';Record 'enable_pass'
    }
    Action 'status';Record 'effective_policy_verified'
    if(Probe '1.1.1.1' 443){throw 'Direct internet bypass'}
    Record 'internet_blocked_without_identity_or_tunnel'
    if(-not (Probe $api.Host $api.Port)){throw 'Bootstrap API blocked'}
    Record 'admission_api_still_reachable'
    $probeName='VanGuardInternetTest-Allow-'+[Guid]::NewGuid().ToString('N')
    try {
        New-NetFirewallRule -PolicyStore PersistentStore -Name $probeName -DisplayName $probeName -Enabled True -Direction Outbound -Action Allow -Protocol TCP -RemoteAddress 1.1.1.1 -RemotePort 443 | Out-Null
        if(Probe '1.1.1.1' 443){throw 'New local allow rule bypasses managed policy'}
        Record 'new_local_allow_cannot_bypass_lockdown'
        Action 'status';Record 'status_verifies_local_rule_merging_disabled'
    } finally {
        Get-NetFirewallRule -PolicyStore PersistentStore -Name $probeName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    }
    if(Test-Path 'C:\Program Files\VanGuardEndpointData\identity'){throw 'Unexpected identity in pre-enrollment test'}
    Record 'no_device_identity_or_certificate_required_to_block'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {
    [pscustomobject]@{environment='Windows native; real firewall and network';cases=$cases;ipv6_connectivity='BELUM_TERUJI';automatic_recovery='test-only separate scheduled task; not a product feature'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $Report -Encoding UTF8
}
