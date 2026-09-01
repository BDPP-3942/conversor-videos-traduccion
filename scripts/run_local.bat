@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
if /I "%~1"=="duplicates" goto dispatch
if /I "%~1"=="reprocess-subtitles" goto dispatch
:dispatch
".venv\Scripts\python.exe" scripts\run_local.py %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
