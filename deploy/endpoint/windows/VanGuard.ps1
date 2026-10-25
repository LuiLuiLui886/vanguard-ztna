param([ValidateSet('configure','status','init','import-bundle','login','connect','disconnect','diagnose','logout')][string]$Action='status')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$guard = $null
$owned = $false
try {
    Assert-Administrator
    Assert-SafePath $DataRoot
    $python = Get-Installation
    # Serialize runtime use against installer/uninstaller. Disconnect/logout must
    # run in a separate terminal during connect, using the client's scoped locks.
    $guard = New-Object Threading.Mutex($false,'Global\VanGuardEndpointSetup')
    if ($Action -notin @('disconnect','logout','status')) {
        $owned = $guard.WaitOne(0)
        if (-not $owned) { throw 'Operasi instalasi/connect lain sedang berjalan.' }
    }
    $identity = Join-Path $DataRoot 'identity'
    $profile = Join-Path $DataRoot 'config\profile.json'
    $trust = Join-Path $DataRoot 'config\root.crt'
    Assert-SafePath $profile
    Assert-SafePath $trust
    if ($Action -eq 'status' -and -not (Test-Path -LiteralPath $profile)) {
        if (Test-Path -LiteralPath $trust) {
            Write-Host 'Konfigurasi belum lengkap. Ulangi configure dengan profil/root dan fingerprint/key yang sama dari admin.'
            exit 1
        }
        Write-Host 'Terpasang; profil tepercaya belum tersedia. Jalankan -Action configure. Belum enrollment/admission.'
        exit 0
    }
    if ($Action -eq 'configure') {
        $source = Read-Host 'Path profil publik dari administrator'
        $root = Read-Host 'Path root.crt dari jalur tepercaya'
        Assert-SafePath $source
        Assert-SafePath $root
        $expectedRoot = Read-Host 'Fingerprint SHA256 Root CA yang dikonfirmasi admin'
        $expectedKey = Read-Host 'Public key WireGuard server yang dikonfirmasi admin'
        Install-TrustedProfile $python $source $root $expectedRoot $expectedKey (Join-Path $DataRoot 'config')
        Write-Host 'Profil tersimpan. Belum ada identitas baru, login, peer atau tunnel.'
        exit 0
    }
    $arguments = @('-m','vanguard.client' ,'--directory',$identity,'--profile',$profile,'--trust',$trust,$Action)
    switch ($Action) {
        'init' {
            $name = Read-Host 'Device ID baru yang dialokasikan admin'
            $ip = Read-Host 'IP tunnel unik yang dikonfirmasi admin (bukan IP LAN)'
            $arguments += @('--device-id',$name,'--tunnel-ip',$ip)
        }
        'import-bundle' { $arguments += @(Read-Host 'Path bundle ZIP publik dari admin') }
        'login' { $arguments += @('--username',(Read-Host 'Username karyawan')) }
        'connect' {
            $addresses = @((Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop) | ForEach-Object { $_.IPAddress + '/' + $_.PrefixLength }) -join ','
            $routes = @((Get-NetRoute -AddressFamily IPv4 -ErrorAction Stop) | ForEach-Object { $_.DestinationPrefix }) -join ','
            if (-not $addresses -or -not $routes) { throw 'Snapshot jaringan tidak lengkap.' }
            Invoke-Checked $python @('-c',"import sys; from vanguard.profile import load_profile,check_network_conflicts; check_network_conflicts(load_profile(sys.argv[1],sys.argv[2]),sys.argv[3].split(','),sys.argv[4].split(','))",$profile,$trust,$addresses,$routes)
            Write-Host 'Terminal ini harus tetap terbuka untuk renewal. Ctrl+C untuk disconnect; logout mencabut sesi server.'
        }
    }
    & $python @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host 'Operasi gagal. Periksa profil/prasyarat dan pesan CLI; jangan hapus config jika cleanup belum terkonfirmasi.'
    exit 1
} finally {
    if ($owned) { $guard.ReleaseMutex() }
    if ($null -ne $guard) { $guard.Dispose() }
}
