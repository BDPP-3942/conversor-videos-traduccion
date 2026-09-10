@echo off
setlocal
cd /d "%~dp0.."
set "CMD=%~1"
if /I "%CMD%"=="reprocess-subtitles" goto reprocess
if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" run --scheduled %*
) else if exist "VideoTranslationPipeline.exe" (
  "VideoTranslationPipeline.exe" run --scheduled %*
) else if exist ".venv\Scripts\python.exe" (
  where uv.exe >nul 2>&1
  if not errorlevel 1 (uv run python main.py run --scheduled %*) else (".venv\Scripts\python.exe" main.py run --scheduled %*)
) else (
  echo [ERROR] Ejecutable, uv o entorno Python no encontrado.
  exit /b 1
)
goto done

:reprocess
if exist "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" (
  "dist\VideoTranslationPipeline\VideoTranslationPipeline.exe" reprocess-subtitles --scheduled %2 %3 %4 %5 %6 %7 %8 %9
) else if exist "VideoTranslationPipeline.exe" (
  "VideoTranslationPipeline.exe" reprocess-subtitles --scheduled %2 %3 %4 %5 %6 %7 %8 %9
) else if exist ".venv\Scripts\python.exe" (
  where uv.exe >nul 2>&1
  if not errorlevel 1 (uv run python main.py reprocess-subtitles --scheduled %2 %3 %4 %5 %6 %7 %8 %9) else (".venv\Scripts\python.exe" main.py reprocess-subtitles --scheduled %2 %3 %4 %5 %6 %7 %8 %9)
) else (
  echo [ERROR] Ejecutable, uv o entorno Python no encontrado.
  exit /b 1
)

done
set CODE=%ERRORLEVEL%
endlocal & exit /b %CODE%
