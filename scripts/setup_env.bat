@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "PYTHON_BIN="

for %%P in (python3.14.exe python3.13.exe python3.12.exe python3.11.exe py.exe python.exe) do (
    if not defined PYTHON_BIN (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            if "%%P"=="py.exe" (
                py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_BIN=py -3.13"
            ) else (
                %%P -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_BIN=%%P"
            )
        )
    )
)

if not defined PYTHON_BIN (
    echo.
    echo [ERROR] Se necesita Python 3.11 o superior.
    echo Instala Python 3.13 desde:
    echo https://www.python.org/downloads/
    exit /b 1
)

echo [INFO] Python seleccionado: %PYTHON_BIN%

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Eliminando entorno virtual incompatible...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creando entorno virtual...
    %PYTHON_BIN% -m venv .venv

    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        exit /b 1
    )
)

echo [INFO] Python del entorno:
".venv\Scripts\python.exe" --version

".venv\Scripts\python.exe" -c "import tomllib"
if errorlevel 1 (
    echo [ERROR] tomllib no esta disponible.
    echo [ERROR] El entorno no usa Python 3.11 o superior.
    exit /b 1
)

echo [INFO] Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo [INFO] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    exit /b 1
)

echo [INFO] Verificando FFmpeg...
".venv\Scripts\python.exe" -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"

if errorlevel 1 (
    echo [ERROR] No se pudo localizar FFmpeg.
    exit /b 1
)

echo [INFO] Ejecutando doctor...
".venv\Scripts\python.exe" main.py doctor

if errorlevel 1 (
    echo [ERROR] El doctor encontro problemas.
    exit /b 1
)

echo.
echo [OK] Entorno preparado correctamente.
endlocal