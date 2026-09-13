@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\hugo.ps1" -Serve %*
exit /b %errorlevel%
