@echo off
REM Hermes Agent on Pagouro: starts the stick's local server if it is not already up, then opens a Hermes chat
REM that uses Pagouro as its model. Nothing about Hermes's normal default model is changed; the overrides live
REM only in this window. Close the window to end the chat; the Pagouro server keeps running until you close
REM its own window or press Ctrl-C there.
setlocal
set PAGOURO_DIR=D:\Pagouro
if not exist "%PAGOURO_DIR%\pagouro.exe" set PAGOURO_DIR=C:\Users\Eric Wade\PAGOURO_BUILD\release\Pagouro
if not exist "%PAGOURO_DIR%\pagouro.exe" (
  echo Pagouro was not found on D:\ or in the local release folder.
  pause
  exit /b 1
)
curl -s --max-time 3 http://127.0.0.1:8484/v1/models >nul 2>&1
if errorlevel 1 (
  echo Starting Pagouro's server from %PAGOURO_DIR% ... about a minute from a USB stick.
  start "Pagouro server" /D "%PAGOURO_DIR%" "%PAGOURO_DIR%\pagouro.exe" --serve --port 8484
  :wait
  timeout /t 5 /nobreak >nul
  curl -s --max-time 3 http://127.0.0.1:8484/v1/models >nul 2>&1
  if errorlevel 1 goto wait
)
echo Pagouro is serving on http://127.0.0.1:8484/v1 - opening Hermes on it.
set OPENAI_BASE_URL=http://127.0.0.1:8484/v1
set OPENAI_API_KEY=none
set PATH=C:\Users\Eric Wade\AppData\Local\hermes\hermes-agent\venv\Scripts;%PATH%
hermes chat --provider openai -m pagouro %*
endlocal
