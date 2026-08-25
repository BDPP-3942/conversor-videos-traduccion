@echo off
setlocal
cd /d "%~dp0.."
call scripts\run_unattended.bat %*
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
