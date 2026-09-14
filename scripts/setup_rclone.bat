@echo off
setlocal
cd /d "%~dp0.."
call "%~dp0lib\resolve_uv.bat"
if errorlevel 1 (
  echo [ERROR] uv no esta instalado. Ejecuta scripts\setup_env.bat primero.
  exit /b 1
)
"%UV_BIN%" run python main.py provider bootstrap
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
