@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
if /I "%~1"=="reprocess-subtitles" (
  ".venv\Scripts\python.exe" main.py %*
) else (
  ".venv\Scripts\python.exe" main.py run %*
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
