@echo off
setlocal
cd /d "%~dp0.."
call "%~dp0lib\resolve_uv.bat"
if errorlevel 1 (echo [ERROR] uv no esta instalado. Ejecuta scripts\setup_env.bat & exit /b 1)
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Ejecuta scripts\setup_env.bat & exit /b 1)
"%UV_BIN%" run python scripts\run_local.py %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
