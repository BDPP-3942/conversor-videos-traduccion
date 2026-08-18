@echo off
SETLOCAL

cd /d "%~dp0\.."

SET VENV_DIR=venv

IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] No existe el venv.
    echo Ejecuta primero:
    echo scripts\setup_env.bat
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

SET /P DRIVE_SOURCE="Introduce el ID de la carpeta ORIGEN de Google Drive: "
SET /P DRIVE_TARGET="Introduce el ID de la carpeta DESTINO de Google Drive: "
SET /P EXEC_MODE="Selecciona modo (LOCAL / PRODUCTION) [LOCAL]: "

IF "%EXEC_MODE%"=="" SET EXEC_MODE=LOCAL

python main.py ^
    --source "%DRIVE_SOURCE%" ^
    --target "%DRIVE_TARGET%" ^
    --mode "%EXEC_MODE%"

SET EXIT_CODE=%ERRORLEVEL%

echo.
echo ==========================================
echo Pipeline finalizado.
echo Exit code: %EXIT_CODE%
echo ==========================================

ENDLOCAL

pause

exit /b %EXIT_CODE%