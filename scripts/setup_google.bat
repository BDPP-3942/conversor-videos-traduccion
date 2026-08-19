@echo off
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta primero scripts\setup_env.bat
  exit /b 1
)
call "venv\Scripts\activate.bat"
python main.py auth google
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
