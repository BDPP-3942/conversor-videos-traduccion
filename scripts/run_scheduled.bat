@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Ejecuta scripts\setup_env.bat --cloud & exit /b 1)
".venv\Scripts\python.exe" main.py run --mode cloud --config config\app.toml %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
