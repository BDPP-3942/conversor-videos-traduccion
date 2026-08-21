@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta scripts\setup_env.bat
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
if errorlevel 1 exit /b 1
if not exist "dist\VideoTranslationPipeline\config" mkdir "dist\VideoTranslationPipeline\config"
if not exist "dist\VideoTranslationPipeline\secrets" mkdir "dist\VideoTranslationPipeline\secrets"
if not exist "dist\VideoTranslationPipeline\storage" mkdir "dist\VideoTranslationPipeline\storage"
if not exist "dist\VideoTranslationPipeline\tools" mkdir "dist\VideoTranslationPipeline\tools"
copy /Y "config\app.toml" "dist\VideoTranslationPipeline\config\app.toml" >nul
copy /Y ".env.example" "dist\VideoTranslationPipeline\.env.example" >nul
xcopy /E /I /Y "storage" "dist\VideoTranslationPipeline\storage" >nul
xcopy /E /I /Y "tools" "dist\VideoTranslationPipeline\tools" >nul
if not exist "dist\VideoTranslationPipeline\storage\input" mkdir "dist\VideoTranslationPipeline\storage\input"
if not exist "dist\VideoTranslationPipeline\storage\output" mkdir "dist\VideoTranslationPipeline\storage\output"
echo [OK] Aplicacion portable creada en dist\VideoTranslationPipeline\
echo [INFO] Para empezar con doble clic, ejecuta el EXE sin argumentos.
echo [INFO] Antes del primer procesamiento cloud, ejecuta provider setup-google o provider setup-rclone una sola vez.
endlocal
