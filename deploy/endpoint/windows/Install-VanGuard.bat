@echo off
setlocal DisableDelayedExpansion
title VanGuard - Instalasi Windows
set "VANGUARD_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "VANGUARD_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
echo VanGuard - paket offline Windows 11 x64
echo Ekstrak seluruh ZIP terverifikasi ke folder baru di C:\Program Files dahulu.
echo Python dan WireGuard akan dipasang bila belum tersedia. Setujui UAC jika diminta.
if not exist "%~dp0Install-VanGuard.ps1" (
  echo ERROR: isi ZIP belum lengkap. Jangan menjalankan BAT langsung dari dalam ZIP.
  set "VANGUARD_EXIT=2"
  goto finish
)
"%VANGUARD_PS%" -NoLogo -NoProfile -File "%~dp0Install-VanGuard.ps1"
set "VANGUARD_EXIT=%ERRORLEVEL%"
:finish
echo.
echo Exit code: %VANGUARD_EXIT%
if "%VANGUARD_EXIT%"=="0" echo Instalasi selesai. Lanjutkan panduan SETUP_WINDOWS untuk konfigurasi dan enrollment.
if "%VANGUARD_EXIT%"=="3010" echo Restart diperlukan. Simpan pekerjaan dan restart sendiri, lalu jalankan installer lagi.
if not "%VANGUARD_EXIT%"=="0" echo Jika policy menolak script, hubungi administrator. Jangan nonaktifkan proteksi mesin.
if /I not "%~1"=="/nopause" pause
exit /b %VANGUARD_EXIT%
