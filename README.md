# Video Translation Pipeline v5

Pipeline multiplataforma para procesar ZIP con vídeo/audio, normalizar medios con FFmpeg, transcribir con Whisper y generar subtítulos traducidos. El origen/destino puede ser local, Google Drive o cualquier backend soportado por rclone.

## Objetivo de operación

El sistema está diseñado para que la autenticación sea administrativa y la ejecución cotidiana sea desatendida.

```text
                    ┌──────────────────────┐
                    │  SETUP ADMINISTRATIVO│
                    ├──────────────────────┤
                    │ Google OAuth          │
                    │ rclone OAuth          │
                    │ carpetas / perfiles   │
                    └──────────┬───────────┘
                               │ persiste
             ┌─────────────────┼──────────────────┐
             ▼                 ▼                  ▼
         token.json        rclone.conf       runtime.toml
             │                 │                  │
             └─────────────────┼──────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ RUN --SCHEDULED      │
                    │ sin interacción      │
                    └──────────┬───────────┘
                               ▼
                    preflight + refresh
                               ▼
                          procesamiento
```

## Uso diario

### Local

Coloca los ZIP en:

```text
storage/input/
```

Arranca:

```bash
python main.py run --scheduled
```

O abre el ejecutable sin argumentos.

### Google Drive

Los ZIP se depositan en la carpeta de entrada configurada en Google Drive. El pipeline conserva el `token.json` y en cada ejecución intenta renovar silenciosamente el access token cuando está caducado y existe refresh token.

### rclone

Los ZIP se depositan en la ruta `source` configurada del remoto activo. El proyecto contiene su propio binario de rclone y su `rclone.conf`. No se exige instalación global.

El preflight hace una lectura de la carpeta de entrada para validar el remoto y dar a rclone la oportunidad de refrescar OAuth cuando el backend lo permite.

## Cambio de proveedor

Los perfiles son persistentes. Puedes configurar varios:

```bash
python main.py provider setup-rclone dropbox_main dropbox --source input --target output
python main.py provider setup-rclone onedrive_main onedrive --source input --target output
```

Cambiar el activo no borra ninguno:

```bash
python main.py provider use rclone --profile onedrive_main --source rclone://input --target rclone://output
```

## Comandos administrativos

```bash
python main.py doctor
python main.py provider list
python main.py provider verify google_drive --profile default
python main.py provider verify rclone --profile dropbox_main --location input
python main.py provider update-rclone --force
```

## Compilación

Windows:

```bat
scripts\build_windows.bat
```

Linux:

```bash
scripts/build_linux.sh
```

El paquete compilado usa el directorio del ejecutable como raíz operativa, por lo que `config/`, `secrets/`, `storage/` y `tools/` viven junto al ejecutable.

## Scheduler de Windows

Se puede crear la tarea mediante:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_task_scheduler.ps1
```

La tarea ejecuta `VideoTranslationPipeline.exe run --scheduled` con el directorio de trabajo de la aplicación.

## Documentación

- `docs/AUDIT.md`: problemas detectados en el proyecto original.
- `docs/SECURITY.md`: secretos, permisos y amenazas relevantes.
- `docs/UNATTENDED.md`: configuración completa del modo desatendido.
- `docs/VERSIONING.md`: estrategia Git y Semantic Versioning.

## Versión de rclone

La release estable de referencia del proyecto es rclone `v1.75.0`, publicada el 31 de julio de 2026.
