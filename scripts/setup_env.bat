@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."

set "INSTALL_CLOUD=false"
set "INSTALL_RCLONE=false"
set "INSTALL_TTS=false"
set "PREFETCH_WHISPER=false"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--cloud" (set "INSTALL_CLOUD=true") else if /I "%~1"=="--rclone" (set "INSTALL_RCLONE=true") else if /I "%~1"=="--tts" (set "INSTALL_TTS=true") else if /I "%~1"=="--prefetch-whisper" (set "PREFETCH_WHISPER=true") else (echo [ERROR] Opcion desconocida: %~1 & exit /b 2)
shift
goto parse_args

:args_done
where uv.exe >nul 2>&1
if errorlevel 1 (
  echo [ERROR] uv no esta instalado. Instala uv y vuelve a ejecutar este script.
  exit /b 1
)
set "PYTHON_VERSION=%PYTHON_VERSION%"
if not defined PYTHON_VERSION set "PYTHON_VERSION=3.13"
if not "%PYTHON_VERSION%"=="3.11" if not "%PYTHON_VERSION%"=="3.12" if not "%PYTHON_VERSION%"=="3.13" (
  echo [ERROR] PYTHON_VERSION debe ser 3.11, 3.12 o 3.13.
  exit /b 2
)

uv --version
uv python install %PYTHON_VERSION%
if errorlevel 1 exit /b 1
uv venv --python %PYTHON_VERSION%
if errorlevel 1 exit /b 1
uv sync --python %PYTHON_VERSION% --group dev
if errorlevel 1 exit /b 1
if "%INSTALL_CLOUD%"=="true" uv sync --python %PYTHON_VERSION% --group dev --extra google
if errorlevel 1 exit /b 1
if "%INSTALL_TTS%"=="true" uv sync --python %PYTHON_VERSION% --group dev --extra tts
if errorlevel 1 exit /b 1

uv run python -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 exit /b 1
if "%INSTALL_RCLONE%"=="true" (
  where rclone >nul 2>&1
  if errorlevel 1 (echo [ERROR] rclone no esta instalado. Ejecuta scripts\setup_rclone.bat & exit /b 1)
)

uv run python scripts\setup_tts.py
if errorlevel 1 exit /b 1
if "%INSTALL_TTS%"=="true" uv run python scripts\setup_tts.py --enable
if errorlevel 1 exit /b 1

uv run python main.py doctor
if errorlevel 1 exit /b 1
if "%PREFETCH_WHISPER%"=="true" (
  echo [INFO] Precargando el modelo Whisper seleccionado automaticamente...
  uv run python main.py prefetch-whisper
  if errorlevel 1 exit /b 1
)

echo.
echo [OK] Entorno preparado correctamente con uv.
endlocal
