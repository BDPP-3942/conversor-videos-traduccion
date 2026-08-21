@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
if not exist "dist\VideoTranslationPipeline\storage\input" mkdir "dist\VideoTranslationPipeline\storage\input"
if not exist "dist\VideoTranslationPipeline\storage\output" mkdir "dist\VideoTranslationPipeline\storage\output"
echo [OK] Ejecutable creado en dist\VideoTranslationPipeline\
endlocal
