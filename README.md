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

El VTT original es la fuente de verdad temporal. La traducción conserva `start/end` y TTS solo acepta VTT válidos. Los silencios entre cues permanecen como silencio en el audio sintetizado.

## Alcance

- Procesamiento por lotes de vídeos y ZIP.
- Entrada/salida local, Google Drive y backends de rclone.
- Normalización y generación audiovisual con FFmpeg.
- STT con Whisper/faster-whisper y segmentación basada en silencios.
- Validación final de intervalos después de la segmentación.
- Traducción con proveedores configurables y fallback.
- VTT, diagnóstico y recuperación de resultados existentes.
- TTS opcional sincronizado con el VTT traducido y validado.
- MP4 TTS y WebM TTS opcional.
- Manifests, resume e idempotencia.
- Deduplicación conservadora.
- Concurrencia de vídeo adaptada a los recursos disponibles.
- Regeneración limpia explícita de resultados existentes mediante el pipeline común.
- CLI, wrappers, ejecutable y ejecución programada.
- CI, auditoría de seguridad y auditoría de dependencias.

No es un editor audiovisual interactivo ni sustituye la revisión humana de traducciones o locuciones.

## Inicio rápido

Consulta [`docs/INSTALLATION.md`](docs/INSTALLATION.md) para instalar dependencias y preparar el entorno.

```bash
python main.py doctor
python main.py run --dry-run
python main.py run
```

Para operación desatendida:

```bash
python main.py run --scheduled
```

## Regeneración completa

Cuando necesitas volver a generar un vídeo cuyo resultado ya existe utilizando **la implementación actual completa del pipeline**, utiliza la operación explícita `REGENERATE FROM ZERO`:

```bash
video-translation-regenerate
```

También puedes indicar las ubicaciones explícitamente:

```bash
video-translation-regenerate \
  --source local://storage/input \
  --target local://storage/output
```

La regeneración no es `resume` ni una recuperación selectiva. Localiza los resultados registrados, los aparta temporalmente mediante backup, fuerza el procesamiento desde la fuente a través de `MediaPipeline` y elimina los backups anteriores únicamente después de completar correctamente la regeneración. La fuente original se conserva. Si el procesamiento falla, los backups se restauran cuando el backend permite la operación de rename.

Consulta [`docs/REGENERATION.md`](docs/REGENERATION.md) para las garantías y limitaciones específicas de local, Google Drive y rclone.

## Reprocesado y recuperación de VTT

Los resultados ya procesados no necesitan volver a pasar por la conversión audiovisual. Si existe el vídeo normal, la recuperación puede reconstruir los subtítulos sin regenerarlo.

```bash
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
python main.py reprocess-subtitles --all
```

Consulta [`docs/SUBTITLES.md`](docs/SUBTITLES.md) y [`docs/RESUME.md`](docs/RESUME.md).

## TTS

TTS está desactivado por defecto. Con `TTS_ENABLED=true`, el pipeline valida/repara los VTT antes de sintetizar y genera los artefactos TTS mediante el mismo proveedor de almacenamiento utilizado por la ejecución.

```dotenv
TTS_ENABLED=true
TTS_REQUIRED=false
TTS_PROVIDER=kokoro
TTS_VOICE=af_sarah
TTS_MODEL_PATH=tools/tts/kokoro-v1.0.onnx
TTS_VOICES_PATH=tools/tts/voices-v1.0.bin
```

La implementación local utiliza Kokoro mediante `kokoro-onnx`. Los extras TTS y los pesos del modelo deben instalarse/proporcionarse cuando TTS está habilitado.

Consulta [`docs/TTS.md`](docs/TTS.md).

## Concurrencia de vídeo

La configuración actual usa `max_parallel_videos = 0` como AUTO. El runtime calcula un límite conservador teniendo en cuenta la configuración efectiva de Whisper, CPU, RAM disponible y, cuando corresponde, memoria GPU. Un valor positivo es un máximo solicitado y puede reducirse si supera el límite seguro; `1` mantiene un único worker.

Esta lógica fue introducida después de la release `1.2.2` por la PR #20 y forma parte de `v1.3.0`.

**Importante para la release 1.4.0:** la CLI debe aplicar el mismo cálculo seguro también cuando se proporciona `--parallel-videos`; el valor solicitado nunca debe saltarse el techo calculado por recursos.

## Almacenamiento y ejecución programada

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

Consulta [`docs/STORAGE.md`](docs/STORAGE.md) y [`docs/SCHEDULING.md`](docs/SCHEDULING.md).

## Calidad

```bash
pytest
ruff check .
ruff check . --select S
ruff format --check .
python -m compileall .
python -m pip check
python -m build
pip-audit
```

La CI además comprueba packaging, entry points, seguridad y dependencias. Consulta [`docs/CI_CD.md`](docs/CI_CD.md).

## Documentación canónica

| Documento | Propósito |
|---|---|
| [`docs/PROJECT.md`](docs/PROJECT.md) | Propósito y alcance |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Arquitectura y componentes |
| [`docs/USE_CASES.md`](docs/USE_CASES.md) | Casos de uso soportados |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | Flujo de procesamiento |
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | Instalación y puesta en marcha |
| [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) | Configuración |
| [`docs/CLI.md`](docs/CLI.md) | CLI |
| [`docs/STT.md`](docs/STT.md) | Transcripción |
| [`docs/SUBTITLES.md`](docs/SUBTITLES.md) | VTT, QA y reparación |
| [`docs/TRANSLATION.md`](docs/TRANSLATION.md) | Traducción |
| [`docs/TRANSLATION_PROVIDERS.md`](docs/TRANSLATION_PROVIDERS.md) | Proveedores y límites del cliente |
| [`docs/TTS.md`](docs/TTS.md) | TTS sincronizado |
| [`docs/STORAGE.md`](docs/STORAGE.md) | Almacenamiento |
| [`docs/RESUME.md`](docs/RESUME.md) | Resume e idempotencia |
| [`docs/DEDUPLICATION.md`](docs/DEDUPLICATION.md) | Deduplicación |
| [`docs/SCHEDULING.md`](docs/SCHEDULING.md) | Ejecución programada |
| [`docs/PACKAGING.md`](docs/PACKAGING.md) | Empaquetado |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Seguridad |
| [`docs/TESTING.md`](docs/TESTING.md) | Tests |
| [`docs/CI_CD.md`](docs/CI_CD.md) | Integración continua |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Desarrollo |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Diagnóstico |
| [`docs/RELEASES.md`](docs/RELEASES.md) | Releases y versionado |
| [`docs/REGENERATION.md`](docs/REGENERATION.md) | Regeneración completa desde la fuente |

Los documentos históricos `PROJECT_GUIDE.md`, `VTT_REPAIR.md`, `UNATTENDED.md` y `VERSIONING.md` se mantienen por compatibilidad de navegación; los documentos anteriores son la referencia canónica para cada tema.

## Versionado

La release publicada anterior es `1.3.0` (`v1.3.0`). Esta rama prepara `1.4.0`, que aún no está publicada. La release candidata incluye la regeneración limpia de la PR #24 y la gobernanza de la PR #25, además de las correcciones de hardening que superen el release gate.

`v1.3.0` apunta al commit histórico `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` y no se modifica.

## Seguridad y licencias

No versionar secretos, tokens ni claves. Los modelos, pesos y voces TTS pueden tener licencias diferentes de las librerías que los ejecutan. Antes de redistribuir el ejecutable o usarlo comercialmente debe revisarse la licencia concreta de cada componente.
