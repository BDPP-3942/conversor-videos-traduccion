@echo off
setlocal
cd /d "%~dp0.."
where uv.exe >nul 2>&1
if errorlevel 1 (echo [ERROR] uv no esta instalado. & exit /b 1)
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Ejecuta scripts\setup_env.bat & exit /b 1)
uv run python scripts\run_local.py %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
