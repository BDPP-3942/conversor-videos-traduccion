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

Los resultados ya procesados no necesitan volver a pasar por la conversión audiovisual. Si existe el vídeo normal, la recuperación puede reconstruir los subtítulos sin regenerarlo.

```bash
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
python main.py reprocess-subtitles --all
```

Los tres casos principales son:

1. **VTT original/STT inválido o ausente:** se reutiliza el vídeo normal, se vuelve a ejecutar STT y después se traduce.
2. **VTT original válido y traducción inválida o ausente:** se conserva el timing original y solo se vuelve a traducir.
3. **Ambos VTT inválidos:** se ejecuta STT una vez y, tras validarlo, se reconstruye la traducción.

Los VTT sustituidos se conservan mediante copias `.bak.*`. La recuperación nunca regenera el vídeo normal.

Consulta [`docs/VTT_REPAIR.md`](docs/VTT_REPAIR.md).

## TTS

TTS está desactivado por defecto. Con `TTS_ENABLED=true`, el pipeline común valida/repara los VTT antes de sintetizar y genera los artefactos TTS mediante el mismo proveedor de almacenamiento utilizado por la ejecución.

```dotenv
TTS_ENABLED=true
TTS_REQUIRED=false
TTS_PROVIDER=kokoro
TTS_VOICE=af_sarah
TTS_MODEL_PATH=tools/tts/kokoro-v1.0.onnx
TTS_VOICES_PATH=tools/tts/voices-v1.0.bin
```

La implementación local utiliza Kokoro mediante `kokoro-onnx`. Los extras TTS y los pesos del modelo deben instalarse/proporcionarse por separado. Un TTS ya válido se reutiliza; si se reparan los VTT, el audio se regenera para mantener sincronización con el nuevo contenido.

Consulta [`docs/TTS.md`](docs/TTS.md) para configuración, sincronización, artefactos, modelos y licencias.

## Primera ejecución y resultados existentes

En una primera ejecución, TTS se ejecuta después de que la carpeta de salida tenga un vídeo normal y el VTT traducido validado.

Para resultados ya procesados, no es necesario volver a colocar todos los vídeos en `storage/input` si el MP4 normal sigue disponible en `storage/output`. Primero revisa duplicados y subtítulos; después utiliza `reprocess-subtitles` o una ejecución con resume.

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

La autenticación cloud se configura antes de una ejecución programada y no debe requerir interacción durante el procesamiento.

## Reanudación

Los artefactos válidos se reutilizan y solo se repiten las etapas que no pueden recuperarse. La reparación de VTT no regenera el vídeo normal. Un fallo TTS no obliga a repetir STT o traducción.

## Ejecución programada y ejecutable

Windows Task Scheduler, macOS launchd, cron y los ejecutables deben utilizar el mismo pipeline, directorio de trabajo determinista, configuración, credenciales y modelos. `--scheduled` evita depender de interacción humana.

## Calidad

La CI comprueba tests, lint, formato, seguridad, compilación, packaging y dependencias. Localmente:

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
| [`docs/VTT_REPAIR.md`](docs/VTT_REPAIR.md) | Validación y recuperación de VTT |
| [`docs/TTS.md`](docs/TTS.md) | TTS, sincronización, artefactos y licencias |
| [`docs/TRANSLATION_PROVIDERS.md`](docs/TRANSLATION_PROVIDERS.md) | Proveedores de traducción y fallback |
| [`docs/UNATTENDED.md`](docs/UNATTENDED.md) | Scheduler y ejecución sin interacción |
| [`docs/DEDUPLICATION.md`](docs/DEDUPLICATION.md) | Deduplicación y limpieza segura |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Seguridad y gestión de secretos |
| [`docs/AUDIT.md`](docs/AUDIT.md) | Auditoría técnica y riesgos conocidos |
| [`docs/RELEASES.md`](docs/RELEASES.md) | Política e histórico de releases |
| [`CHANGELOG.md`](CHANGELOG.md) | Cambios orientados al usuario |

## Versionado

Se usa Semantic Versioning. La línea de producto comienza en `1.0.0`; `1.1.x` contiene correcciones compatibles de esta integración y `1.2.0` queda para la siguiente funcionalidad nueva compatible.

## Seguridad y licencias

No versionar secretos, tokens ni claves. Los modelos, pesos y voces TTS pueden tener licencias diferentes de las librerías que los ejecutan. Antes de redistribuir el ejecutable o usarlo comercialmente debe revisarse la licencia concreta de cada componente.
