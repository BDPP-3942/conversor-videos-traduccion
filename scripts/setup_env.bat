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

rem Prefer the Windows Python launcher. It selects the registered 3.13 runtime
rem and avoids broken python3.13.exe PATH aliases/shims.
set "PYTHON_BIN="
call :find_python
if defined PYTHON_BIN goto python_ready

echo [WARN] No se encontro un interprete Python 3.11-3.13 funcional.
where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No hay Python funcional y tampoco esta disponible WinGet.
    echo [ERROR] Instala Python 3.13 desde python.org o Microsoft Store y vuelve a ejecutar este script.
    exit /b 1
)

echo [INFO] Intentando instalar Python 3.13 mediante WinGet...
winget install --id Python.Python.3.13 -e --scope user --accept-source-agreements --accept-package-agreements --disable-interactivity
if errorlevel 1 (
    echo [ERROR] WinGet no pudo instalar Python 3.13.
    exit /b 1
)

rem Refresh the current PATH with the standard per-user Python locations.
if exist "%LocalAppData%\Programs\Python\Python313" set "PATH=%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python313\Scripts;%PATH%"
if exist "%LocalAppData%\Python\bin" set "PATH=%LocalAppData%\Python\bin;%PATH%"
set "PYTHON_BIN="
call :find_python
if not defined PYTHON_BIN (
    echo [ERROR] Python 3.13 se instalo, pero no se pudo localizar en esta terminal.
    echo [ERROR] Cierra y vuelve a abrir la terminal y ejecuta scripts\setup_env.bat de nuevo.
    exit /b 1
)

:python_ready
echo [INFO] Python seleccionado: %PYTHON_BIN%
%PYTHON_BIN% --version
if errorlevel 1 exit /b 1

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Eliminando entorno virtual incompatible...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creando entorno virtual...
    %PYTHON_BIN% -m venv .venv
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" --version
".venv\Scripts\python.exe" -c "import tomllib"
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if "%INSTALL_CLOUD%"=="true" ".venv\Scripts\python.exe" -m pip install -r requirements-google.txt
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 exit /b 1

if "%INSTALL_RCLONE%"=="true" (
    where rclone >nul 2>&1 || (
        echo [ERROR] rclone no esta instalado. Ejecuta scripts\setup_rclone.bat
        exit /b 1
    )
)

".venv\Scripts\python.exe" main.py doctor
if errorlevel 1 exit /b 1

echo.
echo [OK] Entorno preparado correctamente.
endlocal
exit /b 0

:find_python
rem 1) Python Launcher: reliable for registered Windows Python installations.
where py.exe >nul 2>&1
if not errorlevel 1 (
    py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,13) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_BIN=py -3.13"
        exit /b 0
    )
    py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_BIN=py -3.12"
        exit /b 0
    )
    py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_BIN=py -3.11"
        exit /b 0
    )
)

rem 2) Direct python commands. Broken PATH shims are ignored because the command
rem must actually execute Python and report a supported version.
for %%P in (python.exe python3.13.exe python3.12.exe python3.11.exe python3.exe) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        %%P -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_BIN=%%P"
            exit /b 0
        )
    )
)
exit /b 1
