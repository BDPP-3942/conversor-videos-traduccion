@echo off
where rclone >nul 2>&1 || (echo [ERROR] rclone no esta instalado. Instala rclone desde https://rclone.org/ & exit /b 1)
rclone version
echo [OK] rclone disponible. Ejecuta: rclone config
