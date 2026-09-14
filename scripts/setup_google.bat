@echo off
setlocal
cd /d "%~dp0.."
call "%~dp0lib\resolve_uv.bat"
if errorlevel 1 (echo [ERROR] uv no esta instalado. & exit /b 1)
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Ejecuta primero scripts\setup_env.bat & exit /b 1)
"%UV_BIN%" sync --extra google
if errorlevel 1 exit /b 1
"%UV_BIN%" run python main.py auth google
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
