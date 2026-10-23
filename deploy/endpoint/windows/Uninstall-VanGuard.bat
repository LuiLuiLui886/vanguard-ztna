@echo off
setlocal DisableDelayedExpansion
title VanGuard - Uninstall
set "VANGUARD_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "VANGUARD_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
set "VANGUARD_SCRIPT=%~dp0Uninstall-VanGuard.ps1"
rem Parse the complete block before PowerShell removes this BAT with AppRoot.
(
"%VANGUARD_PS%" -NoLogo -NoProfile -Command "$options=@('-NoLogo','-NoProfile'); if (@(Get-ExecutionPolicy -List | Where-Object { $_.ExecutionPolicy -ne 'Undefined' }).Count -eq 0) { $options+=@('-ExecutionPolicy','RemoteSigned') }; & $env:VANGUARD_PS @options -File $env:VANGUARD_SCRIPT; exit $LASTEXITCODE"
if errorlevel 1 (
  echo Uninstall gagal. Periksa pesan di atas; data tetap dipertahankan.
  if /I not "%~1"=="/nopause" pause
  exit /b 1
)
echo Exit code: 0
if /I not "%~1"=="/nopause" pause
exit /b 0
)
