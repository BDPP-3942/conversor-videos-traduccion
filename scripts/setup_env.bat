@echo off
setlocal
cd /d "%~dp0.."
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python main.py init
python main.py doctor
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
echo Entorno listo.
endlocal
