@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "INSTALL_CLOUD=false"
set "INSTALL_RCLONE=false"
:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--cloud" set "INSTALL_CLOUD=true"
if /I "%~1"=="--rclone" set "INSTALL_RCLONE=true"
if not /I "%~1"=="--cloud" if not /I "%~1"=="--rclone" (echo [ERROR] Opcion desconocida: %~1 & exit /b 2)
shift
goto parse_args
:args_done

set "PYTHON_BIN="
for %%P in (python3.13.exe python3.12.exe python3.11.exe py.exe python.exe) do (
    if not defined PYTHON_BIN (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            if "%%P"=="py.exe" (
                py -3.13 -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_BIN=py -3.13"
            ) else (
                %%P -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_BIN=%%P"
            )
        )
    )
)

if not defined PYTHON_BIN (
    echo [ERROR] Se necesita Python 3.11, 3.12 o 3.13.
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

".venv\Scripts\python.exe" --version
".venv\Scripts\python.exe" -c "import tomllib"
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if "%INSTALL_CLOUD%"=="true" ".venv\Scripts\python.exe" -m pip install -r requirements-google.txt
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 exit /b 1

if "%INSTALL_RCLONE%"=="true" (where rclone >nul 2>&1 || (echo [ERROR] rclone no esta instalado. Ejecuta scripts\setup_rclone.bat & exit /b 1))

".venv\Scripts\python.exe" main.py doctor
if errorlevel 1 exit /b 1

echo.
echo [OK] Entorno preparado correctamente.
endlocal
