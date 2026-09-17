# Referencia de la CLI

La CLI es el contrato de automatización del proyecto. Puede ejecutarse con `python main.py` o mediante los entry points instalados. Esta documentación explica los comandos públicos y su semántica; los nombres exactos de opciones, tipos y valores aceptados siguen definidos por `--help` del parser.

## Ayuda y comandos públicos

```bash
uv run video-translation-pipeline --help
uv run video-translation-pipeline run --help
uv run video-translation-pipeline doctor --help
uv run video-translation-pipeline init --help
uv run video-translation-pipeline prefetch-whisper --help
uv run video-translation-regenerate --help
uv run video-subtitle-qa --help
uv run video-translation-tts --help
```

## `run`

Procesa las entradas configuradas y genera los artefactos del pipeline:

```bash
uv run video-translation-pipeline run
```

Opciones principales:

| Opción | Finalidad | Restricciones / efecto |
| --- | --- | --- |
| `--scheduled` | Ejecuta en modo desatendido. | No abre navegadores ni solicita interacción. |
| `--dry-run` | Comprueba preparación y configuración efectiva. | No procesa medios. |
| `--provider` | Selecciona almacenamiento (`local`, `google_drive`, `gdrive`, `rclone`). | Si se omite se usa la configuración persistida. |
| `--source` | Sobrescribe la entrada. | Debe utilizarse con `--target` cuando se cambia el par de almacenamiento. |
| `--target` | Sobrescribe la salida. | Debe utilizarse con `--source` cuando se cambia el par de almacenamiento. |
| `--no-retain-sources` | Evita conservar fuentes procesadas. | No se permite durante regeneración. |
| `--no-resume` | Desactiva la reutilización de resultados compatibles. | Solo afecta a la ejecución actual. |
| `--no-name-migration` | Desactiva la migración de nombres legacy. | No desactiva la política normal de naming. |
| `--parallel-videos N` | Limita vídeos simultáneos. | `0` significa automático; `1` fuerza un worker. |
| `--translation-batch-size N` | Sobrescribe el lote de traducción. | Se normaliza según las capacidades del proveedor. |
| `--whisper-beam-size N` | Sobrescribe `beam_size`. | Debe ser positivo. |
| `--whisper-cpu-threads N` | Configura hilos CPU de Whisper. | `0` es automático. |
| `--no-ffmpeg-copy` | Desactiva copia directa de streams. | Fuerza la ruta de recodificación configurada. |
| `--generate-webm` | Solicita el WebM secundario. | Es incompatible con `--no-webm`. |
| `--no-webm` | Impide el WebM secundario. | Es incompatible con `--generate-webm`. |

Los ajustes no expuestos por una opción se toman de la configuración de la aplicación.

## Regeneración: `video-translation-regenerate`

Regenera resultados desde la fuente original sin reutilizar resultados compatibles:

```bash
uv run video-translation-regenerate --help
uv run video-translation-regenerate \
  --source local://storage/input \
  --target local://storage/output
```

Admite las opciones de almacenamiento y procesamiento compatibles con la regeneración, incluidas `--provider`, `--source`, `--target`, `--no-name-migration`, `--parallel-videos`, `--translation-batch-size`, `--whisper-beam-size`, `--whisper-cpu-threads`, `--no-ffmpeg-copy`, `--generate-webm` y `--no-webm`.

No acepta deliberadamente `--scheduled`, `--dry-run`, `--no-retain-sources` ni `--no-resume`: la regeneración es una operación forzada distinta. Aparta temporalmente los resultados, ejecuta el `MediaPipeline` común y restaura los anteriores si la operación falla y el backend lo permite.

## Recuperación de subtítulos

```bash
uv run python main.py reprocess-subtitles --help
uv run python main.py reprocess-subtitles --all
uv run python main.py reprocess-subtitles --all --stt-only
uv run python main.py reprocess-subtitles --all --translate-only
```

`--stt-only` y `--translate-only` son mutuamente excluyentes. También existen `--output-folder`, `--all`, `--video`, `--source`, `--scheduled`, `--provider` y `--target`. Esta ruta permite recuperar la transcripción o traducción sin volver a convertir el vídeo cuando los artefactos existentes lo permiten.

## Duplicados

```bash
uv run python main.py duplicates --help
uv run python main.py duplicates scan --help
uv run python main.py duplicates analyze --help
uv run python main.py duplicates delete --help
```

- `scan` localiza candidatos.
- `analyze` genera el análisis persistible.
- `delete --dry-run` muestra el plan sin modificar datos.
- `delete` ejecuta únicamente un plan válido y confirmado.

Ejemplo:

```bash
uv run python main.py duplicates scan --target local://storage/output
uv run python main.py duplicates analyze --target local://storage/output
uv run python main.py duplicates delete --target local://storage/output --dry-run
```

## Proveedores de almacenamiento

```bash
uv run python main.py provider --help
uv run python main.py provider list --help
uv run python main.py provider verify google_drive --help
uv run python main.py provider verify rclone --help
uv run python main.py provider use --help
uv run python main.py provider bootstrap --help
uv run python main.py provider setup-google --help
uv run python main.py provider setup-rclone --help
uv run python main.py provider auth-rclone --help
uv run python main.py provider update-rclone --help
uv run python main.py provider remove --help
```

`bootstrap` prepara el binario gestionado de rclone. `setup-google` y `setup-rclone` realizan la configuración interactiva correspondiente. `verify` comprueba un proveedor sin convertirlo en el proveedor activo. `use` cambia el proveedor seleccionado por la configuración.

## Diagnóstico y preparación

```bash
uv run python main.py doctor --help
uv run python main.py doctor
uv run python main.py init --help
uv run python main.py prefetch-whisper --help
uv run python main.py prefetch-whisper
```

`doctor` valida dependencias, rutas y recursos necesarios. `init` prepara la configuración inicial. `prefetch-whisper` descarga/prepara el modelo seleccionado sin procesar un vídeo.

## TTS

```bash
uv run video-translation-tts --help
```

El entry point de TTS mantiene un contrato separado del procesamiento principal. Las opciones concretas de voz, VTT, vídeo, WebM y configuración deben consultarse mediante `--help`; la GUI utiliza la misma capa de TTS y no implementa un motor paralelo.

## Archivo de contexto de Whisper

`whisper_initial_prompt` admite texto literal o `txt`, `md`, `csv` y `docx`:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

El fichero se resuelve, se valida y su contenido se entrega a Whisper como `initial_prompt`. Esto proporciona contexto de terminología al decodificador y favorece las grafías esperadas, pero no convierte la transcripción en una sustitución literal del audio. La GUI permite seleccionar el fichero.

## Wrappers y programación

Linux/macOS:

```bash
./scripts/run_local.sh run --config ./config/app.toml
./scripts/run_local.sh regenerate --config ./config/app.toml --no-webm
```

Windows:

```bat
scripts\run_local.bat run --config .\config\app.toml
scripts\run_local.bat regenerate --config .\config\app.toml --no-webm
```

La ejecución programada utiliza el mismo dispatcher y conserva el modo `--scheduled` para entornos sin interacción.

## Otros entry points

```bash
uv run video-translation-pipeline --help
uv run video-translation-regenerate --help
uv run video-subtitle-qa --help
uv run video-translation-tts --help
uv run video-translation-desktop
```

## Códigos de salida

`run` devuelve `0` al completar correctamente, `2` ante finalización parcial, `1` ante errores de procesamiento y `3` cuando no se cumplen comprobaciones de preparación. Regeneración devuelve `0` al completar y `3` ante una preparación insuficiente; los errores de sintaxis y de contrato de proveedor producen un código distinto de cero.

## Regla de mantenimiento

Cuando se añada un comando público, primero debe existir en el parser y aparecer correctamente en `--help`; después se documenta aquí con finalidad, efectos y restricciones. No se traducen nombres técnicos, comandos, flags, rutas, APIs, formatos, clases, funciones ni nombres de modelos.

## Documentación relacionada

- [`README.md`](../README.md)
- [`PROJECT.md`](PROJECT.md)
- [`DESKTOP.md`](DESKTOP.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`CONFIGURATION.md`](CONFIGURATION.md)
- [`REGENERATION.md`](REGENERATION.md)
- [`STORAGE.md`](STORAGE.md)
- [`SCHEDULING.md`](SCHEDULING.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
