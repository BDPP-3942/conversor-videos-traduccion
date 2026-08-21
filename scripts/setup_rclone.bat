@echo off
setlocal
cd /d "%~dp0.."
python main.py provider bootstrap
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
