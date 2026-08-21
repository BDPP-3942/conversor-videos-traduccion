@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta primero scripts\setup_env.bat
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-google.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" main.py auth google
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
