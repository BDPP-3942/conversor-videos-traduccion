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

### Reprocesado selectivo de subtítulos

El comando `reprocess-subtitles` trabaja sobre una carpeta de salida que ya existe y no entra en la lógica normal de deduplicación/renombrado. No crea carpetas `_01`, hashes ni variantes derivadas por colisión.

```bash
# Solo Whisper/STT; reutiliza el MP4 existente y no ejecuta FFmpeg
python main.py reprocess-subtitles --output-folder 37x02_Tema --stt-only

# Solo traducción; reutiliza la transcripción existente y no ejecuta Whisper ni FFmpeg
python main.py reprocess-subtitles --output-folder 37x02_Tema --translate-only

# STT + traducción sobre la misma salida
python main.py reprocess-subtitles --output-folder 37x02_Tema

# También puede resolverse por nombre de vídeo o por la ruta `source` registrada en un manifest
python main.py reprocess-subtitles --video 37x02_Tema.mp4 --stt-only
python main.py reprocess-subtitles --source "curso/carpeta/video.mp4" --translate-only
```

Antes de sustituir una transcripción o un VTT se validan existencia, tamaño, sintaxis, cantidad de segmentos y timestamps. La versión anterior queda conservada con un backup versionado (`.bak.<UTC timestamp>`), sin sobrescribir backups previos. Cada operación genera además un registro JSON en `reprocess_history/`.

El diagnóstico de reprocesado compara huecos y solapamientos de timestamps. La traducción conserva los mismos `start/end` que recibe del STT, por lo que un desfase que ya esté presente en esos timestamps apunta al tramo Whisper/VAD/segmentación y no a la traducción.

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


### Perfiles automáticos de CPU y RAM

La configuración `whisper_model = "auto"` activa un perfil de recursos en función de CPU y RAM. Como referencia, un equipo de 24+ GB y 12+ hilos lógicos usa `medium` con `int8` y un único vídeo simultáneo; un equipo Apple Silicon con ~16 GB puede usar también `medium` pero manteniendo un único vídeo; equipos de 8 GB usan `small`. Se evita descargar el modelo de una máquina cuando no es necesario.

El modelo no se incluye dentro del repositorio. `faster-whisper` descarga el modelo al primer uso; puedes forzar esa descarga durante la preparación con `scripts/setup_env.bat --prefetch-whisper` o `./scripts/setup_env.sh --prefetch-whisper`. En CPU, `int8` está soportado por faster-whisper/CTranslate2.

El perfil automático está diseñado para priorizar estabilidad y evitar saturación por ejecutar varios modelos Whisper grandes simultáneamente. `max_parallel_videos = 0` significa automático.
