# Opt-in managed endpoint policy. Windows Firewall persists independently of the client process.
param([ValidateSet('preview','enable','status','attach','detach','recover')][string]$Action='status',
      [switch]$ConfirmRecovery)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$directory=Join-Path $DataRoot 'internet-lockdown'
$statePath=Join-Path $directory 'state.json'
$profilePath=Join-Path $DataRoot 'config\profile.json'
$group='VanGuard Managed Internet v1'
$prefix='VanGuard-Internet-'
$digestNames=@('API','WireGuard','DHCP','Tunnel','IPv6')|ForEach-Object {$prefix+$_}
$quarantine=$prefix+'Quarantine'
$mutex=$null;$owned=$false;$setup=$null;$setupOwned=$false
$script:filterCache=$null
function Read-RuleFilters {
    # One bounded snapshot per filter class, not six CIM calls for EACH rule.
    $script:filterCache=@{}
    foreach($kind in @('Port','Address','Interface','Application','Service')) {
        $map=@{}
        foreach($filter in @(& ('Get-NetFirewall'+$kind+'Filter') -PolicyStore ActiveStore)) {
            if($filter.InstanceID -in $digestNames) {
                if($map.ContainsKey($filter.InstanceID)){throw 'Duplicate firewall filter; inspection uncertain.'}
                $map[$filter.InstanceID]=$filter
            }
        }
        $script:filterCache[$kind]=$map
    }
}
function Rule-Digest($Rule) {
    if($null -eq $script:filterCache){Read-RuleFilters}
    foreach($kind in @('Port','Address','Interface','Application','Service')) {
        if(-not $script:filterCache[$kind].ContainsKey($Rule.Name)){throw 'Firewall filter unavailable.'}
    }
    $port=$script:filterCache.Port[$Rule.Name]
    $address=$script:filterCache.Address[$Rule.Name]
    $interface=$script:filterCache.Interface[$Rule.Name]
    $application=$script:filterCache.Application[$Rule.Name]
    $service=$script:filterCache.Service[$Rule.Name]
    $data=@([string]$Rule.Name,[string]$Rule.Enabled,[string]$Rule.Direction,[string]$Rule.Action,
        [string]$Rule.Profile,[string]$port.Protocol,($port.LocalPort -join ','),($port.RemotePort -join ','),
        ($address.LocalAddress -join ','),($address.RemoteAddress -join ','),
        ($interface.InterfaceAlias -join ','),[string]$application.Program,[string]$service.Service)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($data|ConvertTo-Json -Compress))))).Replace('-','') }
    finally {$sha.Dispose()}
}
function Assert-Policy($State) {
    if($State.schema -ne 2 -or $State.phase -ne 'ACTIVE'){throw 'Lockdown managed belum aktif/masih legacy; lakukan recovery lokal dan enable ulang.'}
    if((Get-FileHash -LiteralPath $profilePath).Hash -ne $State.profile_sha256){throw 'Profil berubah setelah lockdown.'}
    foreach($p in @(Get-NetFirewallProfile -PolicyStore ActiveStore)) {
        if($State.schema -eq 2 -and $p.AllowLocalFirewallRules -ne 'False'){throw 'Local rule merging tidak dinonaktifkan.'}
        if($p.Enabled -ne 'True' -or $p.DefaultOutboundAction -ne 'Block'){throw 'Policy firewall tidak fail-closed.'}
    }
    $allRules=@(Get-NetFirewallRule -PolicyStore ActiveStore)
    foreach($rule in @($allRules | Where-Object {$_.Enabled -eq 'True' -and $_.Direction -eq 'Outbound' -and $_.Action -eq 'Allow'})) {
        if($State.schema -eq 2 -and $rule.PolicyStoreSourceType -eq 'Local'){continue}
        if($rule.Name -notin @($State.rules.PSObject.Properties.Name)){throw 'Allow rule asing aktif; lockdown tidak terkonfirmasi.'}
    }
    Read-RuleFilters
    foreach($item in $State.rules.PSObject.Properties) {
        $found=@($allRules|Where-Object {$_.Name -eq $item.Name})
        if($found.Count -ne 1){throw 'Firewall rule missing or ambiguous.'}
        $rule=$found[0]
        if($State.schema -eq 2 -and $rule.PolicyStoreSourceType -ne 'GroupPolicy'){throw 'Managed rule policy source mismatch.'}
        if((Rule-Digest $rule) -ne $item.Value){throw 'Aturan lockdown berubah atau tidak efektif.'}
    }
    if((Get-Service BFE).Status -ne 'Running' -or (Get-Service MpsSvc).Status -ne 'Running'){throw 'Firewall service tidak aktif.'}
}
function Refresh-Policy {
    Invoke-Checked gpupdate.exe @('/target:computer','/force','/wait:30')
}
function Quarantine([string]$Store='PersistentStore') {
    if(-not (Get-NetFirewallRule -PolicyStore $Store -Name $quarantine -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -PolicyStore $Store -Name $quarantine -DisplayName $quarantine -Group $group -Direction Outbound -Action Block -Profile Any | Out-Null
    }
}
try {
    Assert-Administrator
    Assert-SafePath $DataRoot
    Assert-SafePath $directory
    if($Action -notin @('status','attach','detach')) {
        $setup=New-Object Threading.Mutex($false,'Global\VanGuardEndpointSetup')
        $setupOwned=$setup.WaitOne(0)
        if(-not $setupOwned){throw 'Connect/maintenance sedang aktif.'}
    }
    $mutex=New-Object Threading.Mutex($false,'Global\VanGuardInternetPolicy')
    $owned=$mutex.WaitOne(0)
    if(-not $owned){throw 'Operasi policy lain sedang berjalan.'}
    if($Action -eq 'recover') {
        if(-not $ConfirmRecovery){throw 'Recovery membuka kembali policy lama; perlu -ConfirmRecovery dari administrator lokal.'}
        Assert-NoTunnel
        $state=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
        if($state.schema -notin @(1,2)){throw 'Backup state tidak valid.'}
        $store=if($state.schema -eq 2){'localhost'}else{'PersistentStore'}
        Quarantine
        if($state.schema -eq 2){Quarantine 'localhost';Refresh-Policy}
        foreach($name in $state.disabled_rules) {
            # Preserve edits to unrelated rule contents; restore only Enabled that we changed.
            Get-NetFirewallRule -PolicyStore PersistentStore -Name $name | Enable-NetFirewallRule | Out-Null
        }
        foreach($p in $state.profiles) {
            if($state.schema -eq 2){
                Set-NetFirewallProfile -PolicyStore localhost -Name $p.Name -Enabled $p.Enabled -DefaultOutboundAction $p.DefaultOutboundAction -AllowLocalFirewallRules $p.AllowLocalFirewallRules
            }else{
                Set-NetFirewallProfile -PolicyStore PersistentStore -Name $p.Name -Enabled $p.Enabled -DefaultOutboundAction $p.DefaultOutboundAction
            }
        }
        # Remove only exact owned names, not arbitrary rules or the entire firewall policy.
        foreach($name in $state.owned_names) {
            Get-NetFirewallRule -PolicyStore $store -Name $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
        }
        if($state.schema -eq 2){
            Refresh-Policy
            Get-NetFirewallRule -PolicyStore localhost -Name $quarantine -ErrorAction SilentlyContinue | Remove-NetFirewallRule
            Refresh-Policy
        }
        Get-NetFirewallRule -PolicyStore PersistentStore -Name $quarantine -ErrorAction SilentlyContinue | Remove-NetFirewallRule
        [IO.Directory]::Move($directory,($directory+'-recovered-'+[Guid]::NewGuid().ToString('N')))
        Write-Host 'Policy sebelum lockdown dipulihkan oleh admin lokal; backup/audit dipertahankan. Ini bukan revocation server.'
        exit 0
    }
    if($Action -eq 'detach') {
        $state=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
        if($state.schema -ne 2 -or ($prefix+'Tunnel') -notin $state.owned_names){throw 'Kepemilikan policy tunnel tidak terkonfirmasi.'}
        # Restrict only our own rule; other policy mismatches are not repaired here.
        Set-NetFirewallRule -PolicyStore localhost -Name ($prefix+'Tunnel') -Enabled False -InterfaceAlias Any
        Refresh-Policy
        $script:filterCache=$null
        $state.rules.($prefix+'Tunnel')=Rule-Digest (Get-NetFirewallRule -PolicyStore ActiveStore -Name ($prefix+'Tunnel'))
        Write-State $statePath $state
        Write-Host 'Pengecualian tunnel dinonaktifkan; internet langsung tetap diblokir.'
        exit 0
    }
    if($Action -eq 'attach') {
        $state=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
        Assert-Policy $state
        if(Get-NetFirewallRule -PolicyStore ActiveStore -Name $quarantine -ErrorAction SilentlyContinue){throw 'Quarantine masih aktif.'}
        $deadline=[DateTime]::UtcNow.AddSeconds(10)
        do {
            $adapter=Get-NetAdapter -Name 'vanguard-client' -ErrorAction SilentlyContinue
            if($null -ne $adapter){break}
            Start-Sleep -Milliseconds 200
        } while([DateTime]::UtcNow -lt $deadline)
        if($null -eq $adapter -or $adapter.InterfaceDescription -notlike 'WireGuard Tunnel*' -or
           (Get-Service 'WireGuardTunnel$vanguard-client').Status -ne 'Running') {
            throw 'Adaptor/service WireGuard belum terkonfirmasi; policy tidak dibuka.'
        }
        # No interface exception before admission creates the actual tunnel.
        $store=if($state.schema -eq 2){'localhost'}else{'PersistentStore'}
        Set-NetFirewallRule -PolicyStore $store -Name ($prefix+'Tunnel') -InterfaceAlias 'vanguard-client' -Enabled True
        if($state.schema -eq 2){Refresh-Policy}
        $script:filterCache=$null
        $state.rules.($prefix+'Tunnel')=Rule-Digest (Get-NetFirewallRule -PolicyStore ActiveStore -Name ($prefix+'Tunnel'))
        Write-State $statePath $state
        Assert-Policy $state
        Write-Host 'Pengecualian hanya untuk adaptor WireGuard terkonfirmasi; grant gateway tetap wajib.'
        exit 0
    }
    if($Action -eq 'status') {
        $state=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
        Assert-Policy $state
        if(Get-NetFirewallRule -PolicyStore ActiveStore -Name $quarantine -ErrorAction SilentlyContinue){throw 'Quarantine masih aktif.'}
        Write-Host 'Lockdown aktif; IPv6 diblokir. Status ini bukan bukti admission atau akses internet.'
        exit 0
    }
    Assert-NoTunnel
    $python=Get-Installation
    Invoke-Checked $python @('-c',"from vanguard.profile import load_profile; import sys; p=load_profile(sys.argv[1],sys.argv[2]); assert p.get('schema')==2",$profilePath,(Join-Path $DataRoot 'config\root.crt'))
    $profile=Get-Content -Raw -LiteralPath $profilePath|ConvertFrom-Json
    if(Test-Path -LiteralPath $directory){throw 'State lockdown sudah ada; periksa status/recovery, jangan menimpa backup.'}
    if((Get-CimInstance Win32_ComputerSystem).PartOfDomain){throw 'Endpoint domain memerlukan integrasi administrator organisasi.'}
    if(@(Get-NetFirewallRule -PolicyStore ActiveStore | Where-Object { $_.PolicyStoreSourceType -eq 'GroupPolicy' }).Count){throw 'Policy organisasi ditemukan; perlu integrasi administrator, tidak ditimpa.'}
    if(@(Get-NetFirewallRule -PolicyStore PersistentStore | Where-Object {$_.Name -like ($prefix+'*')}).Count){throw 'Nama rule sudah ada; inspeksi kepemilikan.'}
    if(@(Get-NetFirewallRule -PolicyStore localhost -ErrorAction SilentlyContinue).Count){throw 'Local GPO firewall sudah berisi rule; jangan menimpa policy lain.'}
    $inbound=@(Get-NetFirewallRule -PolicyStore PersistentStore -Enabled True -Direction Inbound)
    $rules=@() # Local allow rules stay intact but are excluded from the effective managed policy.
    $profiles=@(Get-NetFirewallProfile -PolicyStore localhost | Select-Object Name,@{n='Enabled';e={[string]$_.Enabled}},@{n='DefaultOutboundAction';e={[string]$_.DefaultOutboundAction}},@{n='AllowLocalFirewallRules';e={[string]$_.AllowLocalFirewallRules}})
    if($Action -eq 'preview') {
        Write-Host ('Mode terkelola Local GPO: nonaktifkan local rule merging; salin '+$inbound.Count+' rule inbound yang aktif. Blok outbound langsung dan IPv6; DHCP/admission/WireGuard dikecualikan.')
        Write-Host 'Mode ini mengambil alih kebijakan outbound pada perangkat terkelola. Belum diterapkan.'
        exit 0
    }
    Protect-Directory $directory
    $names=@('API','WireGuard','DHCP','Tunnel','IPv6')|ForEach-Object {$prefix+$_}
    $copies=@($inbound|ForEach-Object {@{source=$_.Name;target=($prefix+'Inbound-'+[Guid]::NewGuid().ToString('N'))}})
    $state=@{schema=2;policy_store='localhost';inbound_copies=$copies;phase='PREPARING';created_utc=[DateTime]::UtcNow.ToString('o');profile_sha256=(Get-FileHash $profilePath).Hash;profiles=$profiles;disabled_rules=@($rules|ForEach-Object {$_.Name});owned_names=@($names)+@($copies|ForEach-Object {$_.target});rules=@{}}
    Write-State $statePath $state
    Invoke-Checked netsh.exe @('advfirewall','export',(Join-Path $directory 'before.wfw'))
    Quarantine
    Quarantine 'localhost'
    foreach($copy in $copies){
        Copy-NetFirewallRule -PolicyStore PersistentStore -Name $copy.source -NewPolicyStore localhost -NewName $copy.target | Out-Null
    }
    $api=[Uri]$profile.api_url
    New-NetFirewallRule -PolicyStore localhost -Name ($prefix+'API') -DisplayName ($prefix+'API') -Group $group -Direction Outbound -Action Allow -Profile Any -Protocol TCP -RemoteAddress $api.Host -RemotePort $api.Port | Out-Null
    New-NetFirewallRule -PolicyStore localhost -Name ($prefix+'WireGuard') -DisplayName ($prefix+'WireGuard') -Group $group -Direction Outbound -Action Allow -Profile Any -Protocol UDP -RemoteAddress $profile.wireguard_host -RemotePort $profile.wireguard_port | Out-Null
    New-NetFirewallRule -PolicyStore localhost -Name ($prefix+'DHCP') -DisplayName ($prefix+'DHCP') -Group $group -Direction Outbound -Action Allow -Profile Any -Protocol UDP -LocalPort 68 -RemotePort 67 -Program "$env:SystemRoot\System32\svchost.exe" -Service Dhcp | Out-Null
    # Keep disabled until admission creates the real adapter; Windows rejects absent aliases.
    New-NetFirewallRule -PolicyStore localhost -Name ($prefix+'Tunnel') -DisplayName ($prefix+'Tunnel') -Group $group -Direction Outbound -Action Allow -Profile Any -RemoteAddress '0.0.0.0/1','128.0.0.0/1' -Enabled False | Out-Null
    New-NetFirewallRule -PolicyStore localhost -Name ($prefix+'IPv6') -DisplayName ($prefix+'IPv6') -Group $group -Direction Outbound -Action Block -Profile Any -RemoteAddress '::/1','8000::/1' | Out-Null
    Set-NetFirewallProfile -PolicyStore localhost -Profile Domain,Private,Public -Enabled True -DefaultOutboundAction Block -AllowLocalFirewallRules False
    Refresh-Policy
    foreach($name in $names){$state.rules[$name]=Rule-Digest (Get-NetFirewallRule -PolicyStore ActiveStore -Name $name)}
    $state.phase='ACTIVE'
    Write-State $statePath $state
    Assert-Policy (Get-Content -Raw $statePath|ConvertFrom-Json)
    Get-NetFirewallRule -PolicyStore localhost -Name $quarantine | Remove-NetFirewallRule
    Refresh-Policy
    Get-NetFirewallRule -PolicyStore PersistentStore -Name $quarantine | Remove-NetFirewallRule
    Write-Host 'Lockdown aktif dan persisten. Belum ada internet sebelum admission dan grant server. Penutupan client tidak membuka internet langsung.'
    exit 0
} catch {
    # Never auto-restore outbound access after a partially applied lockdown.
    Write-Host ('Operasi policy gagal: '+$_.Exception.Message)
    Write-Host 'State/backup dipertahankan. Gunakan konsol lokal untuk inspeksi dan recovery admin.'
    exit 1
} finally {
    if($setupOwned){$setup.ReleaseMutex()}
    if($null -ne $setup){$setup.Dispose()}
    if($owned){$mutex.ReleaseMutex()}
    if($null -ne $mutex){$mutex.Dispose()}
}
