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

## Salidas y migración de resultados históricos

Cada vídeo nuevo genera `MP4 + WebM + VTT traducido`, y la transcripción original se guarda en `original_transcriptions/`. El WebM es una copia ligera orientada a servidores con menos recursos.

Los ZIP que ya estaban procesados no vuelven a pasar por conversión, Whisper ni traducción. Con `workflow.rename_processed_duplicates = true`, volver a introducir el ZIP permite ejecutar un flujo de solo renombrado: se extrae temporalmente el contenido, se vuelve a inferir curso/lección/descripción con las reglas actuales y se renombran la carpeta y los artefactos existentes. Esto permite migrar resultados generados antes de incorporar la nueva inferencia de nombres sin rehacer el procesamiento.

La salida WebM se configura con `SECONDARY_VIDEO_*` o con la sección `[ffmpeg]` de `config/app.toml`. Las salidas MP3 antiguas se conservan para compatibilidad con `resume`; no se generan MP3 nuevos.

## Rendimiento

El perfil CPU por defecto usa Whisper `small` + `int8`, `beam_size=1`, sin `condition_on_previous_text`, VAD activo y dos trabajadores locales. FFmpeg usa `medium` por defecto y evita el reencode cuando un MP4 ya puede pasar por `-c copy`. La detección de duplicados exactos utiliza SHA-256 y evita el sondeo visual/audio con FFmpeg; la comparación probabilística más cara solo se usa para candidatos de nombre similares que no coinciden por hash.

### Limpieza automática de duplicados de salida

La ejecución normal del pipeline en proveedor local (`run` y `scripts/run_local.sh`) realiza automáticamente una limpieza de `storage/output` después del procesamiento. No es necesario pasar un parámetro de borrado.

También existe el comando independiente `dedupe-output`, que por defecto aplica la misma política automática:

```bash
python main.py dedupe-output --target "/ruta/absoluta/storage/output"
```

Para inspeccionar decisiones sin borrar nada, se puede usar únicamente cuando se necesite comprobar el comportamiento:

```bash
python main.py dedupe-output --target "/ruta/absoluta/storage/output" --dry-run
```

La identidad del duplicado se calcula mediante SHA-256 de todos los recursos generados de la carpeta. Los nombres no determinan que dos resultados sean duplicados. Una carpeta solo se elimina automáticamente cuando existe otra carpeta con contenido idéntico y una puntuación de nombre estrictamente superior. Si no existe un referente claramente más estable, ambas se conservan.

Las entradas eliminadas del registro `storage/state/media_registry.jsonl` se retiran y quedan auditadas en `storage/state/dedupe_history.jsonl`. Un fallo de la limpieza automática no borra resultados de forma adicional ni convierte un procesamiento correcto en `error`: se registra y el lote queda como `partial`.
