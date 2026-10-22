@echo off
setlocal
powershell.exe -NoLogo -NoProfile -File "%~dp0Install-VanGuard.ps1"
set "VANGUARD_EXIT=%ERRORLEVEL%"
echo.
echo Exit code: %VANGUARD_EXIT%
echo Jika policy menolak script, hubungi administrator. Jangan nonaktifkan proteksi mesin.
pause
exit /b %VANGUARD_EXIT%
