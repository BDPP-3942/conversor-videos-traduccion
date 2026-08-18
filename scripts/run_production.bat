@echo off

SETLOCAL

cd /d "%~dp0\.."

echo ==========================================
echo MEDIA PIPELINE - PRODUCTION
echo ==========================================

MediaPipeline.exe ^
    --source "ID_CARPETA_ORIGEN" ^
    --target "ID_CARPETA_DESTINO" ^
    --mode PRODUCTION

SET EXIT_CODE=%ERRORLEVEL%

echo.
echo Pipeline exit code: %EXIT_CODE%

ENDLOCAL

exit /b %EXIT_CODE%