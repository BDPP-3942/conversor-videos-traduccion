# Video Translation Pipeline

Pipeline multiplataforma para automatizar la localización de vídeos: ingesta, normalización audiovisual, transcripción, traducción, subtítulos, narración TTS sincronizada y entrega local o cloud.

## Qué resuelve

```text
Vídeo / ZIP
   ↓
FFmpeg + validación
   ↓
Whisper / VAD + segmentación por silencios
   ↓
VTT original validado
   ↓
Traducción conservando timestamps
   ↓
VTT traducido validado
   ├────────→ subtítulos
   ├────────→ vídeo normal
   └────────→ TTS opcional
                 ↓
             audio por cue
                 ↓
             MP4 / WebM
```

Los timestamps del VTT original son la fuente de verdad temporal. La traducción conserva esos intervalos y TTS solo acepta VTT válidos.

## Alcance

- Procesamiento por lotes de vídeos y ZIP.
- Entrada/salida local, Google Drive y backends de rclone.
- Normalización y generación audiovisual con FFmpeg.
- STT con Whisper/faster-whisper y segmentación basada en silencios.
- Validación final de timestamps después de la segmentación.
- Traducción con proveedores configurables y fallback.
- VTT, diagnóstico y recuperación de resultados existentes.
- TTS opcional sincronizado con el VTT traducido.
- MP4 TTS y WebM TTS opcional.
- Manifests, resume e idempotencia.
- Deduplicación conservadora.
- CLI, wrappers, ejecutable y ejecución programada.
- CI, auditoría de seguridad y auditoría de dependencias.

No es un editor audiovisual interactivo ni sustituye la revisión humana de traducciones o locuciones.

## Inicio rápido

Consulta [`docs/INSTALLATION.md`](docs/INSTALLATION.md) para instalar dependencias y preparar modelos.

```bash
python main.py doctor
python main.py run --dry-run
python main.py run
```

Para operación desatendida:

```bash
python main.py run --scheduled
```

## Reprocesado y recuperación de VTT

Los resultados ya procesados no necesitan volver a pasar por la conversión audiovisual. Si existe un vídeo normal, el reprocesador puede regenerar el STT cuando el VTT original es inválido y volver a traducir cuando el VTT traducido es inválido.

```bash
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
python main.py reprocess-subtitles --all
```

También se puede seleccionar una carpeta con `--output-folder`, un vídeo con `--video` o un origen mediante `--source`. Los VTT reemplazados se conservan como copias `.bak.<timestamp>`.

Consulta [`docs/VTT_RECOVERY.md`](docs/VTT_RECOVERY.md) para las reglas de recuperación y los tres escenarios soportados.

## TTS

TTS está desactivado por defecto. Con `TTS_ENABLED=true`, `python main.py run` ejecuta después del pipeline de vídeo una fase común que inspecciona las carpetas de salida. Antes de sintetizar, recupera los VTT inválidos cuando sea posible.

```text
TTS_ENABLED=true
TTS_PROVIDER=kokoro
TTS_MODEL_PATH=tools/tts/kokoro-v1.0.onnx
TTS_VOICES_PATH=tools/tts/voices-v1.0.bin
```

La implementación inicial utiliza Kokoro mediante `kokoro-onnx`. Deben instalarse los extras TTS y proporcionar los pesos fuera de Git. Un TTS MP4 ya válido se reutiliza si no ha sido necesario reparar los subtítulos.

Consulta [`docs/TTS.md`](docs/TTS.md).

## Almacenamiento

El núcleo de procesamiento es común a todos los modos:

```text
CLI / wrapper / ejecutable / scheduler
                  ↓
             pipeline común
                  ↓
        adapter de almacenamiento
          ↙                    ↘
       local             Google Drive/rclone
```

La autenticación cloud se configura administrativamente y no debe requerir interacción durante una ejecución programada.

## Reanudación

El sistema reutiliza artefactos válidos y solo repite las etapas que no pueden recuperarse. La reparación de VTT no regenera el vídeo normal. TTS se considera una fase independiente: un fallo TTS no obliga a repetir STT o traducción.

## Ejecución programada y ejecutable

Windows Task Scheduler, macOS launchd, cron y los ejecutables deben utilizar el mismo `main.py`/pipeline, directorio de trabajo determinista, configuración, credenciales y modelos. La opción `--scheduled` impide depender de interacción humana.

## Calidad

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

## Documentación

| Documento | Propósito |
|---|---|
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | Instalación, dependencias, entorno y puesta en marcha |
| [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) | Alcance funcional y funcionamiento completo |
| [`docs/VTT_RECOVERY.md`](docs/VTT_RECOVERY.md) | Validación y recuperación de VTT |
| [`docs/TTS.md`](docs/TTS.md) | TTS, sincronización, artefactos y licencias |
| [`docs/TRANSLATION_PROVIDERS.md`](docs/TRANSLATION_PROVIDERS.md) | Proveedores de traducción y fallback |
| [`docs/UNATTENDED.md`](docs/UNATTENDED.md) | Scheduler y ejecución sin interacción |
| [`docs/DEDUPLICATION.md`](docs/DEDUPLICATION.md) | Deduplicación y limpieza segura |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Seguridad y gestión de secretos |
| [`docs/AUDIT.md`](docs/AUDIT.md) | Auditoría técnica y riesgos conocidos |
| [`docs/RELEASES.md`](docs/RELEASES.md) | Política e histórico de releases |
| [`CHANGELOG.md`](CHANGELOG.md) | Cambios orientados al usuario |

## Versionado

Se usa Semantic Versioning:

- `MAJOR`: incompatibilidades.
- `MINOR`: funcionalidad nueva compatible.
- `PATCH`: correcciones, seguridad, documentación y mantenimiento.

La línea de releases de producto comienza en **1.0.0**. El historial previo del paquete Python en `5.x` se explica en [`docs/RELEASES.md`](docs/RELEASES.md).

## Seguridad y licencias

No versionar secretos, tokens ni claves. Los modelos, pesos y voces TTS pueden tener licencias diferentes de las librerías que los ejecutan. Antes de redistribuir el ejecutable o usarlo comercialmente debe revisarse la licencia concreta de cada componente.
