$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$guard = $null
$owned = $false
try {
    Assert-Administrator
    Assert-SafePath $AppRoot
    Assert-SafePath $DataRoot
    $guard = New-Object Threading.Mutex($false,'Global\VanGuardEndpointSetup')
    $owned = $guard.WaitOne(0)
    if (-not $owned) { throw 'Connect/instalasi masih aktif; hentikan dengan launcher pemilik.' }
    Assert-NoTunnel
    if ((Get-Content -LiteralPath (Join-Path $AppRoot '.vanguard-endpoint-owner') -Raw) -ne 'VanGuardEndpoint-schema1') { throw 'Kepemilikan instalasi tidak cocok.' }
    # Do not follow any reparse point or delete an unrelated runtime.
    foreach ($item in Get-ChildItem -LiteralPath $AppRoot -Recurse -Force) { Assert-SafePath $item.FullName }
    Remove-Item -LiteralPath $AppRoot -Recurse -Force
    Write-Host 'Binary aplikasi dihapus. Identitas/config/log tetap disimpan; Python dan WireGuard bersama tidak dihapus.'
    Write-Host 'Penghapusan lokal bukan revocation server. Hubungi admin untuk decommission.'
    exit 0
} catch { Write-Host 'Uninstall tidak selesai; state dipertahankan untuk inspeksi.'; exit 1 }
finally {
    if ($owned) { $guard.ReleaseMutex() }
    if ($null -ne $guard) { $guard.Dispose() }
}
