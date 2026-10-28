# Per-device offline setup. Public provisioning only; no management credential or CA key.
param([switch]$Elevated,[switch]$PrepareOnly,[string]$ExpectedManifestSha256='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$wizard=$null;$wizardOwned=$false;$guard=$null;$owned=$false
$phase='preflight';$statePath=Join-Path $DataRoot 'wizard-state.json'
function Save-Phase([string]$Name) {
    $script:phase=$Name
    Write-State $statePath @{schema=1;phase=$Name;manifest_sha256=$manifestHash;updated_utc=[DateTime]::UtcNow.ToString('o')}
}
function Child-Arguments([string]$Script) {
    $result='-NoProfile -File "'+$Script+'"'
    if((Get-ExecutionPolicy -Scope Process) -eq 'RemoteSigned'){$result='-NoProfile -ExecutionPolicy RemoteSigned -File "'+$Script+'"'}
    return $result
}
try {
    Assert-SafePath $PSScriptRoot
    foreach($name in @('provision.json','profile.json','root.crt','manifest.json')) {
        if(-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $name))){throw 'Paket per-device belum lengkap; minta admin menyiapkan profil dan alokasi perangkat.'}
    }
    $who=[Security.Principal.WindowsIdentity]::GetCurrent()
    if(-not ([Security.Principal.WindowsPrincipal]$who).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        if($Elevated){throw 'Elevasi tidak berhasil.'}
        $arguments=(Child-Arguments $PSCommandPath)+' -Elevated'
        if($PrepareOnly){$arguments+=' -PrepareOnly'}
        if($ExpectedManifestSha256){
            if($ExpectedManifestSha256 -notmatch '^[a-fA-F0-9]{64}$'){throw 'Fingerprint manifest tidak valid.'}
            $arguments+=' -ExpectedManifestSha256 '+$ExpectedManifestSha256
        }
        try{$child=Start-Process "$PSHOME\powershell.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru;exit $child.ExitCode}
        catch{Write-Host 'UAC dibatalkan atau tidak tersedia.';exit 1223}
    }
    Assert-Administrator
    $wizard=New-Object Threading.Mutex($false,'Global\VanGuardEndpointWizard')
    $wizardOwned=$wizard.WaitOne(0)
    if(-not $wizardOwned){throw 'Setup terpadu lain sedang berjalan.'}
    $manifestPath=Join-Path $PSScriptRoot 'manifest.json'
    $manifestHash=(Get-FileHash -LiteralPath $manifestPath).Hash.ToLowerInvariant()
    if($ExpectedManifestSha256 -and ($ExpectedManifestSha256 -notmatch '^[a-fA-F0-9]{64}$' -or $ExpectedManifestSha256 -ne $manifestHash)){throw 'Fingerprint manifest tidak cocok.'}
    $manifest=Get-Content -Raw -LiteralPath $manifestPath|ConvertFrom-Json
    if($manifest.schema -ne 1 -or $manifest.target -ne 'cp313-win_amd64' -or $manifest.signed -ne $false){throw 'Manifest tidak sesuai.'}
    foreach($name in @('provision.json','profile.json','root.crt','Setup-VanGuard.ps1','Install-VanGuard.ps1','Common.ps1')){
        if($null -eq $manifest.files.PSObject.Properties[$name]){throw 'Input wajib tidak tercakup checksum paket.'}
    }
    foreach($entry in $manifest.files.PSObject.Properties){
        if($entry.Name -notmatch '^(?:(?:wheels|runtimes)/)?[a-zA-Z0-9_.-]+$' -or $entry.Value -notmatch '^[a-f0-9]{64}$'){throw 'Path/hash paket tidak valid.'}
        $file=Join-Path $PSScriptRoot $entry.Name;Assert-SafePath $file
        if((Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $entry.Value){throw 'Checksum paket gagal; berhenti tanpa perubahan.'}
    }
    Write-Host 'Gunakan paket per-device dan checksum ZIP dari admin tepercaya. Persetujuan UAC/login tetap diperlukan.'
    $current=Join-Path $AppRoot 'current.json';$reuse=$false
    if(Test-Path -LiteralPath $current){
        $record=Get-Content -Raw -LiteralPath $current|ConvertFrom-Json
        if($record.release -like ($manifestHash+'-*')){$null=Get-Installation;$reuse=$true}
    }
    if(-not $reuse){
        $phase='install-runtime'
        $arguments=(Child-Arguments (Join-Path $PSScriptRoot 'Install-VanGuard.ps1'))+' -Elevated -ExpectedManifestSha256 '+$manifestHash
        $installer=Start-Process "$PSHOME\powershell.exe" -ArgumentList $arguments -Wait -PassThru
        if($installer.ExitCode -ne 0){exit $installer.ExitCode}
    }
    $python=Get-Installation
    $guard=New-Object Threading.Mutex($false,'Global\VanGuardEndpointSetup')
    $owned=$guard.WaitOne(0)
    if(-not $owned){throw 'Instalasi/connect lain sedang berjalan.'}
    Assert-NoTunnel
    # Resume is based on verified files, not merely a prior phase marker.
    foreach($name in @('Common.ps1','VanGuard.ps1','VanGuard.bat','Internet-Lockdown.ps1')){
        if((Get-FileHash (Join-Path $AppRoot $name)).Hash.ToLowerInvariant() -ne $manifest.files.$name){throw 'Launcher terpasang berbeda dari paket; inspeksi maintenance.'}
    }
    Save-Phase 'CONFIGURING'
    $provision=Join-Path $PSScriptRoot 'provision.json'
    $public=Get-Content -Raw -LiteralPath $provision|ConvertFrom-Json
    $sourceProfile=Join-Path $PSScriptRoot 'profile.json';$sourceRoot=Join-Path $PSScriptRoot 'root.crt'
    Invoke-Checked $python @('-c','import sys; from vanguard.provision import load_provision; load_provision(*sys.argv[1:])',$provision,$sourceProfile,$sourceRoot)
    Install-TrustedProfile $python $sourceProfile $sourceRoot $public.root_sha256 $public.server_public_key (Join-Path $DataRoot 'config')
    $profile=Join-Path $DataRoot 'config\profile.json';$trust=Join-Path $DataRoot 'config\root.crt';$identity=Join-Path $DataRoot 'identity'
    $mode=(Get-Content -Raw -LiteralPath $profile|ConvertFrom-Json).schema
    if($mode -eq 2){
        Save-Phase 'MANAGED_POLICY'
        Write-Host 'Profil admin memakai internet terkelola: internet langsung diblok sampai admission dan izin gateway. Recovery hanya oleh admin lokal.'
        $guard.ReleaseMutex();$owned=$false
        $action=if(Test-Path (Join-Path $DataRoot 'internet-lockdown')){'status'}else{'enable'}
        & powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File (Join-Path $AppRoot 'Internet-Lockdown.ps1') -Action $action
        if($LASTEXITCODE -ne 0){throw 'Policy belum terkonfirmasi; state/backup dipertahankan.'}
        $owned=$guard.WaitOne(0);if(-not $owned){throw 'Operasi lain sedang berjalan.'};Assert-NoTunnel
    }
    Save-Phase 'PREPARING_IDENTITY'
    $export=Join-Path $DataRoot 'enrollment-request.json'
    Invoke-Checked $python @('-m','vanguard.provision','--provision',$provision,'--profile',$profile,'--trust',$trust,'--directory',$identity,'--export',$export)
    if(-not (Test-Path (Join-Path $identity 'device.crt'))){
        Save-Phase 'WAITING_APPROVAL'
        Write-Host "Kirim HANYA berkas publik ini ke admin untuk pendaftaran: $export"
        Write-Host 'Admin mengikat akun karyawan, menerbitkan sertifikat dari CA yang ada, lalu mengembalikan bundle publik. Jangan kirim folder identity.'
        $bundle=Join-Path $DataRoot 'approval.zip'
        if(-not (Test-Path $bundle)){
            if($PrepareOnly){exit 20}
            $bundle=Read-Host 'Path bundle ZIP dari admin (Enter untuk berhenti dan lanjutkan BAT yang sama nanti)'
            if(-not $bundle){exit 20}
        }
        Assert-SafePath $bundle
        Invoke-Checked $python @('-m','vanguard.client','--directory',$identity,'--profile',$profile,'--trust',$trust,'import-bundle',$bundle)
    }
    Save-Phase 'READY_FOR_LOGIN'
    if($PrepareOnly){Write-Host 'Endpoint siap login; belum ada admission/tunnel.';exit 0}
    Write-Host 'Sertifikat tersedia. Login karyawan tetap wajib; password tidak dimasukkan ke paket.'
    $username=Read-Host 'Username karyawan dari admin'
    Invoke-Checked $python @('-m','vanguard.client','--directory',$identity,'--profile',$profile,'--trust',$trust,'login','--username',$username)
    Save-Phase 'CONNECTING'
    $guard.ReleaseMutex();$owned=$false
    & powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File (Join-Path $AppRoot 'VanGuard.ps1') -Action connect
    $result=$LASTEXITCODE
    # The connect command owns tunnel cleanup; never delete its config here.
    if($result -eq 0){Save-Phase 'DISCONNECTED'}else{Save-Phase 'CONNECT_FAILED'}
    exit $result
} catch {
    Write-Host "Setup berhenti pada tahap $phase. Config/key/state dipertahankan; jangan hapus tunnel atau identitas."
    Write-Host $_.Exception.Message
    exit 1
} finally {
    if($owned){$guard.ReleaseMutex()}
    if($null -ne $guard){$guard.Dispose()}
    if($wizardOwned){$wizard.ReleaseMutex()}
    if($null -ne $wizard){$wizard.Dispose()}
}
