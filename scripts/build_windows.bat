@echo off
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
call "venv\Scripts\activate.bat"
python -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
if not exist "dist\VideoTranslationPipeline\storage\input" mkdir "dist\VideoTranslationPipeline\storage\input"
if not exist "dist\VideoTranslationPipeline\storage\output" mkdir "dist\VideoTranslationPipeline\storage\output"
echo Ejecutable creado en dist\VideoTranslationPipeline\
endlocal
