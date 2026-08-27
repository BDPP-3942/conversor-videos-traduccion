@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
if /I "%~1"=="tts" (
  shift
  ".venv\Scripts\python.exe" -m src.tts_cli %1 %2 %3 %4 %5 %6 %7 %8 %9
) else if /I "%~1"=="reprocess-subtitles" (
  ".venv\Scripts\python.exe" main.py %*
) else if /I "%~1"=="duplicates" (
  ".venv\Scripts\python.exe" main.py %*
) else (
  ".venv\Scripts\python.exe" main.py run %*
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
