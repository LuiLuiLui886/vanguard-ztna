@echo off
setlocal DisableDelayedExpansion
title VanGuard - Setup Terpadu
set "VANGUARD_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "VANGUARD_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
echo VanGuard - paket offline Windows 10/11 x64
echo Ekstrak seluruh ZIP terverifikasi ke folder baru di C:\Program Files dahulu.
echo Python dan WireGuard akan dipasang bila belum tersedia. Setujui UAC jika diminta.
if not exist "%~dp0Setup-VanGuard.ps1" (
  echo ERROR: isi ZIP belum lengkap. Jangan menjalankan BAT langsung dari dalam ZIP.
  set "VANGUARD_EXIT=2"
  goto finish
)
set "VANGUARD_SCRIPT=%~dp0Setup-VanGuard.ps1"
set "VANGUARD_PREPARE_ONLY=0"
if /I "%~1"=="/prepare-only" set "VANGUARD_PREPARE_ONLY=1"
if /I "%~2"=="/prepare-only" set "VANGUARD_PREPARE_ONLY=1"
"%VANGUARD_PS%" -NoLogo -NoProfile -Command "$options=@('-NoLogo','-NoProfile'); if (@(Get-ExecutionPolicy -List | Where-Object { $_.ExecutionPolicy -ne 'Undefined' }).Count -eq 0) { Write-Host 'Policy default Windows: RemoteSigned hanya untuk proses ini.'; $options+=@('-ExecutionPolicy','RemoteSigned') }; $scriptArgs=@(); if ($env:VANGUARD_PREPARE_ONLY -eq '1') { $scriptArgs+=@('-PrepareOnly') }; & $env:VANGUARD_PS @options -File $env:VANGUARD_SCRIPT @scriptArgs; exit $LASTEXITCODE"
set "VANGUARD_EXIT=%ERRORLEVEL%"
:finish
echo.
echo Exit code: %VANGUARD_EXIT%
if "%VANGUARD_EXIT%"=="0" echo Setup selesai. Status koneksi mengikuti hasil admission, bukan sekadar instalasi.
if "%VANGUARD_EXIT%"=="3010" echo Restart diperlukan. Simpan pekerjaan dan restart sendiri, lalu jalankan installer lagi.
if "%VANGUARD_EXIT%"=="20" echo Menunggu bundle persetujuan admin. Jalankan BAT yang sama lagi setelah bundle tersedia.
if "%VANGUARD_EXIT%"=="1" echo Tahap belum selesai. State dipertahankan; periksa pesan di atas.
if /I not "%~1"=="/nopause" if /I not "%~2"=="/nopause" pause
exit /b %VANGUARD_EXIT%
