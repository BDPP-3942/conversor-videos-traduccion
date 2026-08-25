@echo off
setlocal
cd /d "%~dp0.."
if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" reprocess-subtitles %*
) else if exist "VideoTranslationPipeline.exe" (
  "VideoTranslationPipeline.exe" reprocess-subtitles %*
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py reprocess-subtitles %*
) else (
  echo [ERROR] Ejecutable o entorno Python no encontrado.
  exit /b 1
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
