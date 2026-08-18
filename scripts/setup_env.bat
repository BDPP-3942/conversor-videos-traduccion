@echo off
SETLOCAL EnableDelayedExpansion

cd /d "%~dp0\.."
SET VENV_DIR=venv

IF NOT EXIST "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual en Windows...
    python -m venv %VENV_DIR%
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        exit /b %ERRORLEVEL%
    )
) ELSE (
    echo [INFO] El entorno virtual ya existe.
)

echo [INFO] Activando entorno e instalando dependencias desde requirements.txt...
call %VENV_DIR%\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [OK] Entorno virtual Windows desplegado correctamente.
ENDLOCAL
pause