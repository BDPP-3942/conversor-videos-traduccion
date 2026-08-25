@echo off
setlocal
cd /d "%~dp0.."
set "NO_WEBM=0"
if /I "%~1"=="--no-webm" set "NO_WEBM=1"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline --collect-all faster_whisper --collect-all ctranslate2 --collect-all deep_translator main.py
if errorlevel 1 exit /b 1
if not exist "dist\VideoTranslationPipeline\config" mkdir "dist\VideoTranslationPipeline\config"
if not exist "dist\VideoTranslationPipeline\secrets" mkdir "dist\VideoTranslationPipeline\secrets"
if not exist "dist\VideoTranslationPipeline\storage" mkdir "dist\VideoTranslationPipeline\storage"
if not exist "dist\VideoTranslationPipeline\tools" mkdir "dist\VideoTranslationPipeline\tools"
copy /Y "config\app.toml" "dist\VideoTranslationPipeline\config\app.toml" >nul
if "%NO_WEBM%"=="1" (
  powershell -NoProfile -Command "(Get-Content -Raw 'dist\VideoTranslationPipeline\config\app.toml').Replace('generate_webm = true','generate_webm = false') | Set-Content -NoNewline 'dist\VideoTranslationPipeline\config\app.toml'"
)
copy /Y ".env.example" "dist\VideoTranslationPipeline\.env.example" >nul
xcopy /E /I /Y "storage" "dist\VideoTranslationPipeline\storage" >nul
xcopy /E /I /Y "tools" "dist\VideoTranslationPipeline\tools" >nul
for %%D in (input work output archive failures logs state) do if not exist "dist\VideoTranslationPipeline\storage\%%D" mkdir "dist\VideoTranslationPipeline\storage\%%D"
if "%NO_WEBM%"=="1" echo [INFO] WebM secundario desactivado en la configuracion empaquetada.
echo [OK] Aplicacion portable creada en dist\VideoTranslationPipeline\
echo [INFO] Diagnostico: dist\VideoTranslationPipeline\VideoTranslationPipeline.exe doctor
echo [INFO] Precarga: scripts\prefetch_whisper.bat
echo [INFO] El modelo Whisper no se incluye en el EXE; se descarga en la cache del usuario.
echo [INFO] Task Scheduler: scripts\install_task_scheduler.ps1
endlocal
