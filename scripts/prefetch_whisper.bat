@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py prefetch-whisper
) else if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" prefetch-whisper
) else if exist "VideoTranslationPipeline.exe" (
  "VideoTranslationPipeline.exe" prefetch-whisper
) else (
  echo [ERROR] No se encuentra ni el entorno Python ni el ejecutable.
  exit /b 1
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
