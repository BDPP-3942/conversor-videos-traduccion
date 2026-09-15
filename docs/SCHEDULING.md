# Programación y ejecución desatendida

La aplicación separa la administración interactiva del procesamiento desatendido.

## Comando programado

```bash
python main.py run --scheduled
```

El modo programado utiliza la configuración guardada del proveedor activo y no abre un navegador ni solicita entrada interactiva.

## Integraciones de scheduler compatibles

Los scripts del repositorio proporcionan soporte para:

- Windows Task Scheduler (`scripts/install_task_scheduler.ps1`);
- `launchd` de macOS (`scripts/install_launchd.sh`);
- ejecución de tipo cron en Linux/macOS;
- wrappers de ejecución desatendida bajo `scripts/run_unattended.*` y `scripts/run_scheduled.*`.

Un proceso programado debe tener un directorio de trabajo determinista, acceso a configuración/secretos/modelos, permisos de escritura para el estado y los logs del runtime, y el entorno de Python previsto o un ejecutable empaquetado.

## Autenticación en la nube

Google Drive utiliza credenciales OAuth persistentes y renovación silenciosa cuando es posible. rclone gestiona las credenciales OAuth de sus remotes. La ejecución programada nunca realiza consentimiento interactivo; si una credencial requiere una nueva autorización, la comprobación de disponibilidad falla en su lugar.

## Concurrencia

El pipeline utiliza un bloqueo de runtime. No configures varias tareas independientes del scheduler para procesar simultáneamente el mismo directorio de runtime.
