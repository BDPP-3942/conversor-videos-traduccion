@echo off
setlocal
cd /d "%~dp0.."
if exist "VideoTranslationPipeline.exe" (
  "VideoTranslationPipeline.exe" run --scheduled
) else if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" run --scheduled
) else (
  if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Ejecutable o entorno Python no encontrado.
    exit /b 1
  )
  ".venv\Scripts\python.exe" main.py run --scheduled
)
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
