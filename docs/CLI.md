# Referencia de la CLI

La interfaz de línea de comandos (CLI) es el contrato de automatización del proyecto. Puede ejecutarse desde la raíz del repositorio con `python main.py` o mediante los puntos de entrada instalados con `video-translation-pipeline`.

## Comandos principales

```bash
python main.py --help
python main.py run --help
python main.py doctor --help
python main.py init --help
python main.py prefetch-whisper --help
```

Todo comando que exponga `--help` forma parte del contrato público de la CLI. El analizador de argumentos es la fuente de verdad para nombres, tipos, elecciones y valores aceptados; esta documentación explica su finalidad y los casos de uso.

### Procesamiento: `run`

Procesamiento normal:

```bash
python main.py run
```

Comprobación previa sin modificar vídeos:

```bash
python main.py run --dry-run
```

Ejecución desatendida:

```bash
python main.py run --scheduled
```

#### Opciones de `run`

| Opción | Valor / predeterminado | Descripción |
| --- | --- | --- |
| `--scheduled` | indicador; desactivado por defecto | Ejecuta el proceso como tarea desatendida. No abre navegadores ni solicita interacción. Usa la configuración persistida. |
| `--dry-run` | indicador; desactivado por defecto | Comprueba la preparación del entorno y muestra la configuración efectiva sin procesar archivos. |
| `--provider` | `local`, `google_drive`, `gdrive`, `rclone` | Selecciona el proveedor de almacenamiento para la ejecución. Si se omite, utiliza el configurado. |
| `--source` | URI de almacenamiento | Sobrescribe la ubicación de entrada configurada. Se utiliza junto con `--target`. |
| `--target` | URI de almacenamiento | Sobrescribe la ubicación de salida configurada. Se utiliza junto con `--source`. |
| `--no-retain-sources` | indicador | Evita conservar los archivos fuente después de un procesamiento local normal. No está permitido durante una regeneración. |
| `--no-resume` | indicador | Desactiva la reutilización de resultados compatibles para esta ejecución. No se aplica a regeneración. |
| `--no-name-migration` | indicador | Desactiva la normalización de nombres legacy durante esta ejecución. |
| `--parallel-videos N` | entero; `0 = AUTO` | Solicita el máximo de vídeos simultáneos. El runtime puede reducirlo según los recursos disponibles. `1` fuerza un único worker. |
| `--translation-batch-size N` | entero | Sobrescribe el tamaño de lote utilizado por el proveedor de traducción. |
| `--whisper-beam-size N` | entero | Sobrescribe el tamaño de haz de Whisper. |
| `--whisper-cpu-threads N` | entero; `0` = automático | Sobrescribe el número de hilos de CPU de Whisper. Los valores negativos se normalizan a `0`. |
| `--no-ffmpeg-copy` | indicador | Desactiva la optimización de copia directa de streams de FFmpeg y fuerza el comportamiento de recodificación configurado. |
| `--generate-webm` | indicador | Solicita la generación del WebM secundario. Es incompatible con `--no-webm`. |
| `--no-webm` | indicador | Impide generar el WebM secundario. Es incompatible con `--generate-webm`. |

Los parámetros que no tengan una opción explícita en la CLI se obtienen de la configuración de la aplicación.

### Regeneración completa

Para volver a generar resultados existentes desde la fuente original, sin reutilizar resultados compatibles:

```bash
video-translation-regenerate --help
video-translation-regenerate
```

También pueden indicarse las ubicaciones:

```bash
video-translation-regenerate \
  --source local://storage/input \
  --target local://storage/output
```

La regeneración reutiliza las mismas opciones de configuración compatibles con `run`:

```text
--provider
--source
--target
--no-name-migration
--parallel-videos
--translation-batch-size
--whisper-beam-size
--whisper-cpu-threads
--no-ffmpeg-copy
--generate-webm
--no-webm
```

No acepta deliberadamente `--scheduled`, `--dry-run`, `--no-retain-sources` ni `--no-resume`, porque esas opciones representan contratos de ejecución distintos de la regeneración forzada.

La regeneración aparta temporalmente los resultados existentes, fuerza el procesamiento desde la fuente mediante el `MediaPipeline` común y elimina las copias anteriores únicamente cuando la regeneración termina correctamente. La fuente original se conserva. Si el proceso falla y el backend lo permite, los resultados anteriores se restauran.

Consulta [`REGENERATION.md`](REGENERATION.md).

### Recuperación de subtítulos

Procesar todos los resultados elegibles:

```bash
python main.py reprocess-subtitles --all
```

Regenerar únicamente la transcripción:

```bash
python main.py reprocess-subtitles --all --stt-only
```

Regenerar únicamente la traducción:

```bash
python main.py reprocess-subtitles --all --translate-only
```

Para consultar todas las opciones:

```bash
python main.py reprocess-subtitles --help
```

La orden admite `--stt-only` y `--translate-only` de forma mutuamente excluyente, además de `--output-folder`, `--all`, `--video`, `--source`, `--scheduled`, `--provider` y `--target`.

### Gestión de duplicados

Consultar ayuda general y específica:

```bash
python main.py duplicates --help
python main.py duplicates scan --help
python main.py duplicates analyze --help
python main.py duplicates delete --help
```

Ejemplos:

```bash
python main.py duplicates scan --target local://storage/output
python main.py duplicates analyze --target local://storage/output
python main.py duplicates delete --target local://storage/output --dry-run
python main.py duplicates delete --target local://storage/output
```

`scan` localiza candidatos, `analyze` genera el análisis y `delete --dry-run` muestra qué se eliminaría sin modificar archivos. La eliminación real requiere el plan persistido correspondiente.

### Proveedores de almacenamiento

```bash
python main.py provider --help
python main.py provider list --help
python main.py provider verify google_drive --help
python main.py provider verify rclone --help
python main.py provider use --help
```

El proyecto también dispone de `provider bootstrap`, `provider setup-google`, `provider setup-rclone`, `provider auth-rclone`, `provider update-rclone` y `provider remove`. Las opciones exactas de cada subcomando se consultan con su propio `--help`.

### Diagnóstico y preparación

```bash
python main.py doctor --help
python main.py doctor
python main.py init --help
python main.py prefetch-whisper --help
python main.py prefetch-whisper
```

`doctor` comprueba la preparación del entorno. `init` inicializa la configuración cuando corresponde y `prefetch-whisper` prepara el modelo de Whisper configurado.

### Otros puntos de entrada

```bash
video-translation-pipeline --help
video-translation-regenerate --help
video-subtitle-qa --help
video-translation-tts --help
```

Los cuatro puntos de entrada se instalan desde `pyproject.toml` y mantienen contratos independientes para el procesamiento principal, regeneración, QA de subtítulos y TTS.

## Wrappers multiplataforma

Los wrappers locales delegan en el mismo dispatcher y conservan los argumentos recibidos.

Linux/macOS:

```bash
./scripts/run_local.sh run --config ./config/app.toml
./scripts/run_local.sh regenerate --config ./config/app.toml --no-webm
```

Windows:

```powershell
.\scripts\run_local.bat run --config .\config\app.toml
.\scripts\run_local.bat regenerate --config .\config\app.toml --no-webm
```

`run` es el subcomando explícito y también el comportamiento predeterminado cuando el primer argumento es una opción. `regenerate` se elimina únicamente en el nivel del wrapper antes de delegar en `src.regeneration`.

## Archivo de contexto de Whisper

`whisper_initial_prompt` admite texto literal o una ruta a un archivo `txt`, `md`, `csv` o `docx`.

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

La GUI permite seleccionar ese archivo mediante un diálogo. El contenido se convierte en la cadena que espera Whisper.

## Ejemplos de flujos habituales

### Procesamiento local normal

```bash
uv run video-translation-pipeline run
```

### Comprobación previa

```bash
uv run video-translation-pipeline run --dry-run
```

### Procesamiento con más paralelismo y lote de traducción

```bash
uv run video-translation-pipeline run --parallel-videos 2 --translation-batch-size 32
```

### Desactivar la reutilización de resultados

```bash
uv run video-translation-pipeline run --no-resume
```

### Desactivar la migración de nombres legacy

```bash
uv run video-translation-pipeline run --no-name-migration
```

### Ejecutar con directorios locales explícitos

```bash
uv run video-translation-pipeline run \
  --provider local \
  --source local://storage/input \
  --target local://storage/output
```

### Preparar el modelo local de traducción

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/manage_local_translation.py download
```

### Consultar la ayuda completa de la aplicación

```bash
uv run video-translation-pipeline --help
```

Para documentar una opción nueva, primero debe incorporarse a la ayuda del parser y después a este documento. No se mantienen manualmente dos contratos de argumentos.

## Códigos de salida

`run` devuelve `0` cuando termina correctamente, `2` para finalización parcial, `1` para errores de procesamiento y `3` cuando no se cumplen las comprobaciones de preparación. Regeneración devuelve `0` al completarse y `3` si no se cumplen las comprobaciones de preparación; los errores de sintaxis o de contrato de proveedor producen un código distinto de cero.

## Documentación relacionada

- [`README.md`](../README.md): visión general y comienzo rápido.
- [`PROJECT.md`](PROJECT.md): alcance y arquitectura del proyecto.
- [`DESKTOP.md`](DESKTOP.md): aplicación de escritorio y empaquetado.
- [`INSTALLATION.md`](INSTALLATION.md): instalación y preparación.
- [`CONFIGURATION.md`](CONFIGURATION.md): configuración.
- [`REGENERATION.md`](REGENERATION.md): regeneración completa.
- [`STORAGE.md`](STORAGE.md): almacenamiento y proveedores.
- [`SCHEDULING.md`](SCHEDULING.md): ejecución programada.
- [`TESTING.md`](TESTING.md): estrategia de pruebas.
- [`CI_CD.md`](CI_CD.md): integración y publicación continua.
