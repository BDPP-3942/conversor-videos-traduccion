@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."

set "INSTALL_CLOUD=false"
set "INSTALL_RCLONE=false"
set "INSTALL_TTS=false"
set "PREFETCH_WHISPER=false"
set "INSTALL_LOCAL_TRANSLATION=false"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--cloud" (set "INSTALL_CLOUD=true") else if /I "%~1"=="--rclone" (set "INSTALL_RCLONE=true") else if /I "%~1"=="--tts" (set "INSTALL_TTS=true") else if /I "%~1"=="--prefetch-whisper" (set "PREFETCH_WHISPER=true") else if /I "%~1"=="--local-translation" (set "INSTALL_LOCAL_TRANSLATION=true") else (echo [ERROR] Opcion desconocida: %~1 & exit /b 2)
shift
goto parse_args

:args_done
set "LOCAL_UV_DIR=%CD%\tools\uv"
set "LOCAL_UV_BIN=%LOCAL_UV_DIR%\uv.exe"

if exist "%LOCAL_UV_BIN%" (
  set "UV_BIN=%LOCAL_UV_BIN%"
  echo [INFO] Usando uv gestionado por el proyecto: %UV_BIN%
  goto uv_ready
)

where uv.exe >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%U in ('where uv.exe') do if not defined UV_BIN set "UV_BIN=%%U"
  echo [INFO] Usando uv disponible en PATH: %UV_BIN%
  goto uv_ready
)

echo [INFO] uv no esta disponible en PATH; instalando una copia gestionada en tools\uv\...
if not exist "%LOCAL_UV_DIR%" mkdir "%LOCAL_UV_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $env:UV_UNMANAGED_INSTALL='%LOCAL_UV_DIR%'; irm https://astral.sh/uv/install.ps1 | iex"
if errorlevel 1 (
  echo [ERROR] No se pudo instalar uv en %LOCAL_UV_DIR%.
  exit /b 1
)
if not exist "%LOCAL_UV_BIN%" (
  echo [ERROR] El instalador de uv termino sin producir %LOCAL_UV_BIN%.
  exit /b 1
)
set "UV_BIN=%LOCAL_UV_BIN%"
echo [OK] uv instalado localmente: %UV_BIN%

:uv_ready
set "PYTHON_VERSION=%PYTHON_VERSION%"
if not defined PYTHON_VERSION set "PYTHON_VERSION=3.13"
if not "%PYTHON_VERSION%"=="3.11" if not "%PYTHON_VERSION%"=="3.12" if not "%PYTHON_VERSION%"=="3.13" (
  echo [ERROR] PYTHON_VERSION debe ser 3.11, 3.12 o 3.13.
  exit /b 2
)

"%UV_BIN%" --version
if errorlevel 1 exit /b 1
"%UV_BIN%" python install %PYTHON_VERSION%
if errorlevel 1 exit /b 1
"%UV_BIN%" venv --python %PYTHON_VERSION%
if errorlevel 1 exit /b 1
"%UV_BIN%" sync --python %PYTHON_VERSION% --group dev
if errorlevel 1 exit /b 1
if "%INSTALL_CLOUD%"=="true" "%UV_BIN%" sync --python %PYTHON_VERSION% --group dev --extra google
if errorlevel 1 exit /b 1
if "%INSTALL_TTS%"=="true" "%UV_BIN%" sync --python %PYTHON_VERSION% --group dev --extra tts
if errorlevel 1 exit /b 1

"%UV_BIN%" run python -c "import imageio_ffmpeg; print('[OK] FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 exit /b 1
if "%INSTALL_RCLONE%"=="true" (
  echo [INFO] Preparando el binario rclone gestionado por el proyecto...
  "%UV_BIN%" run python main.py provider bootstrap
  if errorlevel 1 exit /b 1
)

"%UV_BIN%" run python scripts\setup_tts.py
if errorlevel 1 exit /b 1
if "%INSTALL_TTS%"=="true" "%UV_BIN%" run python scripts\setup_tts.py --enable
if errorlevel 1 exit /b 1

"%UV_BIN%" run python main.py doctor
if errorlevel 1 exit /b 1
if "%PREFETCH_WHISPER%"=="true" (
  echo [INFO] Precargando el modelo Whisper seleccionado automaticamente...
  "%UV_BIN%" run python main.py prefetch-whisper
  if errorlevel 1 exit /b 1
)
if "%INSTALL_LOCAL_TRANSLATION%"=="true" (
  echo [INFO] Preparando el modelo de traduccion local fijado...
  "%UV_BIN%" run python scripts\manage_local_translation.py download
  if errorlevel 1 exit /b 1
  "%UV_BIN%" run python scripts\manage_local_translation.py status
  if errorlevel 1 exit /b 1
)

echo.
echo [OK] Entorno preparado correctamente con uv.
endlocal
