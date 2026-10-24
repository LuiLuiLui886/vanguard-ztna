# OS capability gate shared by preview/install and native regression tests.
function Assert-SupportedWindows($OperatingSystem, [bool]$Is64Bit, [string]$Architecture) {
    $version = [version]$OperatingSystem.Version
    $build = [int]$OperatingSystem.BuildNumber
    $windows10 = $build -in @(19044,19045)
    $windows11 = $build -ge 22000
    if ([int]$OperatingSystem.ProductType -ne 1 -or $version.Major -ne 10 -or
        -not $Is64Bit -or $Architecture -ne 'AMD64' -or -not ($windows10 -or $windows11)) {
        throw 'Memerlukan Windows 10 21H2/22H2 atau Windows 11 x64 (client); ARM64/x86/Windows Server tidak didukung paket ini.'
    }
    if ($windows10) { Write-Host 'Target Windows 10 x64. Kompatibilitas aplikasi tidak membuktikan status pembaruan keamanan OS.' }
}
