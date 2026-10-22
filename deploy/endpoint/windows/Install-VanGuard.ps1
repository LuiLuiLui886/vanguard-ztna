# Offline pilot installer. No VM/network provisioning, downloads or identity creation.
param([switch]$Elevated, [switch]$Preview)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$phase = 'preflight'
$guard = $null
$owned = $false
try {
    # The package must be staged by the operator under an administrator-only path.
    Assert-SafePath $PSScriptRoot
    if ($Preview) {
        Write-Host 'Preview: Windows 11 x64; Python 3.13 x64 dan WireGuard resmi harus sudah terpasang.'
        Write-Host 'Offline. Tidak mengubah jaringan, key, CA, login atau tunnel.'
        Write-Host "Runtime: $AppRoot ; config/identity/log: $DataRoot"
        exit 0
    }
    $who = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]$who).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        if ($Elevated) { throw 'Elevasi tidak berhasil.' }
        $arguments = '-NoProfile -File "' + $PSCommandPath + '" -Elevated'
        try {
            $child = Start-Process -FilePath "$PSHOME\powershell.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
            exit $child.ExitCode
        } catch { Write-Host 'UAC dibatalkan atau tidak tersedia.'; exit 1223 }
    }
    Assert-Administrator
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64' -or
        [int](Get-CimInstance Win32_OperatingSystem).BuildNumber -lt 22000) { throw 'Kandidat hanya untuk Windows 11 x64.' }
    Assert-SafePath $AppRoot
    Assert-SafePath $DataRoot
    $guard = New-Object Threading.Mutex($false,'Global\VanGuardEndpointSetup')
    $owned = $guard.WaitOne(0)
    if (-not $owned) { throw 'Operasi VanGuard lain sedang berjalan.' }
    Assert-NoTunnel
    $manifestPath = Join-Path $PSScriptRoot 'manifest.json'
    $approved = Read-Host 'SHA256 manifest yang diterima melalui jalur admin tepercaya'
    if ($approved -notmatch '^[0-9a-fA-F]{64}$' -or
        (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -ne $approved) { throw 'Manifest tidak cocok dengan fingerprint tepercaya.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 1 -or $manifest.target -ne 'cp313-win_amd64' -or $manifest.signed -ne $false) { throw 'Manifest tidak cocok.' }
    foreach ($entry in $manifest.files.PSObject.Properties) {
        if ($entry.Name -notmatch '^(?:wheels/)?[a-zA-Z0-9_.-]+$' -or $entry.Value -notmatch '^[0-9a-f]{64}$') { throw 'Path/hash manifest tidak valid.' }
        $file = Join-Path $PSScriptRoot $entry.Name
        Assert-SafePath $file
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw 'Integritas paket gagal; jangan lanjut.' }
    }
    $python = Read-Host 'Path lengkap python.exe 3.13 x64 yang sudah diverifikasi operator'
    Assert-SafePath $python
    Invoke-Checked $python @('-c',"import sys,struct; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8")
    $wg = Join-Path $env:ProgramFiles 'WireGuard\wireguard.exe'
    Assert-SafePath $wg
    $sig = Get-AuthenticodeSignature -LiteralPath $wg
    $publisher = Read-Host 'Thumbprint sertifikat penanda tangan WireGuard yang dikonfirmasi admin (40 hex)'
    if ($publisher -notmatch '^[0-9a-fA-F]{40}$' -or $sig.Status -ne 'Valid' -or $sig.SignerCertificate.Thumbprint -ne $publisher -or $sig.SignerCertificate.Subject -notmatch 'WireGuard') { throw 'WireGuard resmi dengan signature valid diperlukan.' }
    foreach ($dir in @($AppRoot,$DataRoot)) {
        if ((Test-Path -LiteralPath $dir) -and -not (Test-Path -LiteralPath (Join-Path $dir '.vanguard-endpoint-owner'))) {
            throw 'Direktori sudah ada tanpa marker kepemilikan; inspeksi dahulu.'
        }
        if ((Test-Path -LiteralPath $dir) -and
            (Get-Content -LiteralPath (Join-Path $dir '.vanguard-endpoint-owner') -Raw) -ne 'VanGuardEndpoint-schema1') {
            throw 'Marker kepemilikan berbeda; jangan menimpa instalasi lain.'
        }
        Protect-Directory $dir
        [IO.File]::WriteAllText((Join-Path $dir '.vanguard-endpoint-owner'),'VanGuardEndpoint-schema1')
    }
    Protect-Directory (Join-Path $DataRoot 'config')
    Protect-Directory (Join-Path $DataRoot 'logs')
    $phase = 'install-runtime'
    $release = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() + '-' + [Guid]::NewGuid().ToString('N')
    $releasePath = Join-Path $AppRoot ('releases\'+$release)
    Protect-Directory (Join-Path $AppRoot 'releases')
    # Each attempt uses a fresh runtime. Interrupted/old releases remain evidence;
    # reinstall/repair never runs code from an incomplete previous staging area.
    Protect-Directory $releasePath
    Write-State (Join-Path $DataRoot 'setup-state.json') @{schema=1;status='IN_PROGRESS';phase=$phase;release=$release}
    Invoke-Checked $python @('-m','venv',(Join-Path $releasePath 'venv'))
    $candidate = Join-Path $releasePath 'venv\Scripts\python.exe'
    Invoke-Checked $candidate @('-m','pip','install','--no-index','--no-deps','--require-hashes','--find-links',
        (Join-Path $PSScriptRoot 'wheels'),'-r',(Join-Path $PSScriptRoot 'requirements.lock'))
    Invoke-Checked $candidate @('-m','pip','check')
    Invoke-Checked $candidate @('-m','vanguard.client','--help')
    $phase = 'publish'
    foreach ($file in @('Common.ps1','VanGuard.ps1','Uninstall-VanGuard.ps1')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination (Join-Path $AppRoot $file) -Force
    }
    Write-State (Join-Path $AppRoot 'current.json') @{schema=1;release=$release;version=$manifest.version}
    Write-State (Join-Path $DataRoot 'setup-state.json') @{schema=1;status='INSTALLED';phase='needs-profile-and-enrollment';release=$release}
    Write-Host 'Aplikasi terpasang. Profil tepercaya, enrollment dan login masih diperlukan. Tidak ada peer/tunnel dibuat.'
    Write-Host "Launcher: $AppRoot\VanGuard.ps1"
    exit 0
} catch {
    Write-Host "Gagal pada langkah $phase. Key/config lama dipertahankan. Periksa README dan setup-state.json jika sudah dibuat."
    exit 1
} finally {
    if ($owned) { $guard.ReleaseMutex() }
    if ($null -ne $guard) { $guard.Dispose() }
}
