# Runtime installers are bundled, hash-pinned and signed; never downloaded here.
function Assert-Publisher([string]$Path, [string]$Publisher) {
    Assert-SafePath $Path
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid' -or
        $signature.SignerCertificate.Subject -notmatch ('(?:^|,\s*)O="?' + [regex]::Escape($Publisher) + '"?(?:,|$)')) {
        throw "Tanda tangan/publisher tidak sesuai: $Publisher. Periksa waktu dan trust Windows."
    }
}
function Invoke-RuntimeInstaller([string]$Exe, [string]$Arguments) {
    $process = Start-Process -FilePath $Exe -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -in @(3010,1641)) {
        throw 'REBOOT_REQUIRED: runtime meminta restart. Simpan pekerjaan, restart sendiri, lalu jalankan installer lagi.'
    }
    if ($process.ExitCode -eq 1618) { throw 'Installer Windows lain sedang berjalan. Tunggu lalu ulangi.' }
    if ($process.ExitCode -ne 0) { throw "Pemasangan runtime gagal, exit code $($process.ExitCode)." }
}
function Ensure-Runtimes([string]$Package) {
    $lock = Get-Content -LiteralPath (Join-Path $Package 'runtime-lock.json') -Raw | ConvertFrom-Json
    foreach ($item in @($lock.python,$lock.wireguard)) {
        if ($item.file -notmatch '^runtimes/[a-zA-Z0-9_.-]+$' -or $item.sha256 -notmatch '^[0-9a-f]{64}$') {
            throw 'Manifest runtime tidak valid.'
        }
        $file = Join-Path $Package $item.file
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $item.sha256) { throw 'Hash runtime tidak cocok.' }
    }
    $pythonInstaller = Join-Path $Package $lock.python.file
    $wgInstaller = Join-Path $Package $lock.wireguard.file
    Assert-Publisher $pythonInstaller 'Python Software Foundation'
    Assert-Publisher $wgInstaller 'WireGuard LLC'
    # Reuse a verified all-users CPython 3.13. Do not replace per-user or other runtimes.
    $python = Join-Path $env:ProgramFiles 'Python313\python.exe'
    $registered = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Python\PythonCore\3.13\InstallPath' -ErrorAction SilentlyContinue
    if ($null -ne $registered -and $registered.PSObject.Properties['ExecutablePath']) {
        $python = [string]$registered.ExecutablePath
    }
    Assert-SafePath $python
    if (-not (Test-Path -LiteralPath $python)) {
        if ($null -ne $registered) { throw 'Registrasi Python lama tidak lengkap; perbaiki runtime tersebut dahulu.' }
        $pythonHome = Split-Path -Parent $python
        if (Test-Path -LiteralPath $pythonHome) { throw 'Folder Python sudah ada tetapi runtime tidak lengkap; tidak ditimpa.' }
        Write-Host 'Memasang Python dari paket offline...'
        Invoke-RuntimeInstaller $pythonInstaller ('/quiet /norestart InstallAllUsers=1 TargetDir="' + $pythonHome + '" PrependPath=0 AppendPath=0 Include_launcher=0 AssociateFiles=0 Shortcuts=0 Include_test=0 Include_doc=0 Include_tcltk=0 Include_pip=1 Include_dev=0 Include_debug=0 Include_symbols=0')
    } else { Write-Host 'Python yang sudah terpasang akan digunakan; tidak di-upgrade otomatis.' }
    Assert-Publisher $python 'Python Software Foundation'
    Invoke-Checked $python @( '-c',"import sys,struct,ssl,venv,ensurepip; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8")
    $wg = Join-Path $env:ProgramFiles 'WireGuard\wireguard.exe'
    Assert-SafePath $wg
    if (-not (Test-Path -LiteralPath $wg)) {
        if (Test-Path -LiteralPath (Split-Path -Parent $wg)) { throw 'Folder WireGuard parsial ditemukan; periksa sebelum repair.' }
        Write-Host 'Memasang WireGuard dari paket offline...'
        Invoke-RuntimeInstaller "$env:SystemRoot\System32\msiexec.exe" ('/i "' + $wgInstaller + '" /qn /norestart DO_NOT_LAUNCH=1')
    } else { Write-Host 'WireGuard yang sudah terpasang dipertahankan.' }
    Assert-Publisher $wg 'WireGuard LLC'
    $wgVersion = [version](Get-Item -LiteralPath $wg).VersionInfo.ProductVersion
    if ($wgVersion -lt [version]$lock.wireguard.version) { throw 'WireGuard terlalu lama; upgrade terverifikasi oleh admin diperlukan.' }
    return $python
}
