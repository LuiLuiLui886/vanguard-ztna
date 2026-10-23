@echo off
setlocal DisableDelayedExpansion
title VanGuard - Client Windows
set "VANGUARD_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "VANGUARD_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
set "VANGUARD_SCRIPT=%~dp0VanGuard.ps1"
set "VANGUARD_ACTION=%~1"
if not defined VANGUARD_ACTION (
  echo Pilih: status, configure, init, import-bundle, diagnose, login, connect, disconnect, logout
  set /p "VANGUARD_ACTION=Action [status]: "
)
if not defined VANGUARD_ACTION set "VANGUARD_ACTION=status"
"%VANGUARD_PS%" -NoLogo -NoProfile -Command "$options=@('-NoLogo','-NoProfile'); if (@(Get-ExecutionPolicy -List | Where-Object { $_.ExecutionPolicy -ne 'Undefined' }).Count -eq 0) { $options+=@('-ExecutionPolicy','RemoteSigned') }; & $env:VANGUARD_PS @options -File $env:VANGUARD_SCRIPT -Action $env:VANGUARD_ACTION; exit $LASTEXITCODE"
set "VANGUARD_EXIT=%ERRORLEVEL%"
echo Exit code: %VANGUARD_EXIT%
if /I not "%~2"=="/nopause" pause
exit /b %VANGUARD_EXIT%
