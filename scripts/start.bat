@echo off
setlocal
cd /d "%~dp0.."
if exist "VideoTranslationPipeline.exe" (
  start "Video Translation Pipeline" /wait "VideoTranslationPipeline.exe"
) else if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  start "Video Translation Pipeline" /wait "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe"
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py run --scheduled
) else (
  echo [ERROR] Ejecutable o Python no encontrado.
  exit /b 1
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
