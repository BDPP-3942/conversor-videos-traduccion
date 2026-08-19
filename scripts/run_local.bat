@echo off
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
  echo [ERROR] No existe venv. Ejecuta scripts\setup_env.bat
  exit /b 1
)
call "venv\Scripts\activate.bat"
python main.py run --provider local
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
