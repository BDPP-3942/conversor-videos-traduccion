@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_local.py %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
