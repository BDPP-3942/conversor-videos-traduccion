@echo off
setlocal
cd /d "%~dp0.."
where uv.exe >nul 2>&1
if errorlevel 1 (
  echo [ERROR] uv no esta instalado. Ejecuta scripts\setup_env.bat primero.
  exit /b 1
)
uv run python main.py provider bootstrap
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
