@echo off
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" exit /b 1
"venv\Scripts\python.exe" main.py run --config config\app.toml
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
