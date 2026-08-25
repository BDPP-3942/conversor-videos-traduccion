@echo off
setlocal
cd /d "%~dp0.."
call scripts\run_local.bat %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
