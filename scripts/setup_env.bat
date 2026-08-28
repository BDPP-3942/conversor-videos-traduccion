@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."

set "INSTALL_CLOUD=false"
set "INSTALL_RCLONE=false"
set "INSTALL_TTS=false"
set "PREFETCH_WHISPER=false"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--cloud" (
    set "INSTALL_CLOUD=true"
) else if /I "%~1"=="--rclone" (
    set "INSTALL_RCLONE=true"
) else if /I "%~1"=="--tts" (
    set "INSTALL_TTS=true"
) else if /I "%~1"=="--prefetch-whisper" (
    set "PREFETCH_WHISPER=true"
) else (
    echo [ERROR] Opcion desconocida: %~1
    exit /b 2
)
shift
goto parse_args

:args_done
set "PYTHON_BIN="
where py.exe >nul 2>&1
if not errorlevel 1 (
    py -3.13 -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_BIN=py -3.13"
)

if not defined PYTHON_BIN (
    for %%P in (python3.13.exe python3.12.exe python3.11.exe python.exe) do (
        if not defined PYTHON_BIN (
            where %%P >nul 2>&1
            if not errorlevel 1 (
                %%P -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_BIN=%%P"
            )
        )
    )
)

if not defined PYTHON_BIN (
    where winget.exe >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] No se encontro Python funcional. Intentando instalar Python 3.13 con WinGet...
        winget install --id Python.Python.3.13 -e --scope user --accept-source-agreements --accept-package-agreements --disable-interactivity
        if errorlevel 1 exit /b 1
        where py.exe >nul 2>&1
        if not errorlevel 1 (
            py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,13) else 1)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_BIN=py -3.13"
        )
    )
)

if not defined PYTHON_BIN (
    echo [ERROR] Se necesita Python 3.11, 3.12 o 3.13 y no se encontro un interprete funcional.
    exit /b 1
)

echo [INFO] Python seleccionado: %PYTHON_BIN%
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
    if errorlevel 1 rmdir /s /q ".venv"
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON_BIN% -m venv .venv
    if errorlevel 1 exit /b 1
)

set "VENV_PY=.venv\Scripts\python.exe"
"%VENV_PY%" --version
"%VENV_PY%" -c "import tomllib" >nul 2>&1
if errorlevel 1 exit /b 1
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if "%INSTALL_CLOUD%"=="true" "%VENV_PY%" -m pip install -r requirements-google.txt
if errorlevel 1 exit /b 1
if "%INSTALL_RCLONE%"=="true" "%VENV_PY%" -m pip install -r requirements-rclone.txt
if errorlevel 1 exit /b 1

"%VENV_PY%" -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 exit /b 1

if "%INSTALL_RCLONE%"=="true" (
    where rclone >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] rclone no esta instalado. Ejecuta scripts\setup_rclone.bat
        exit /b 1
    )
)

"%VENV_PY%" scripts\setup_tts.py
if errorlevel 1 exit /b 1
if "%INSTALL_TTS%"=="true" "%VENV_PY%" scripts\setup_tts.py --enable
if errorlevel 1 exit /b 1

"%VENV_PY%" main.py doctor
if errorlevel 1 exit /b 1

if "%PREFETCH_WHISPER%"=="true" (
    echo [INFO] Precargando el modelo Whisper seleccionado automaticamente...
    "%VENV_PY%" main.py prefetch-whisper
    if errorlevel 1 exit /b 1
)

echo.
echo [OK] Entorno preparado correctamente.
endlocal
