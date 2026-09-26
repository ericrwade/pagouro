@echo off
rem Check this copy of Pagouro against MANIFEST.md without installing anything (uses Windows PowerShell).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify_manifest.ps1" -Folder "%~dp0."
echo.
pause
