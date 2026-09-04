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
- Prompt inicial de Whisper mediante texto literal o archivos `txt`, `md`, `csv` y `docx`.
- Validación final de intervalos después de la segmentación.
- Recuperación limitada de segmentos STT sospechosos mediante una política configurable.
- Traducción con proveedores configurables y fallback, incluido proveedor local opcional.
- Traducción local offline español→inglés mediante CTranslate2 + SentencePiece una vez preparado el modelo fijado.
- VTT, diagnóstico y recuperación de resultados existentes.
- TTS opcional sincronizado con el VTT traducido y validado.
- MP4 TTS y WebM TTS opcional.
- Manifests, resume e idempotencia.
- Deduplicación conservadora.
- Concurrencia de vídeo adaptada a los recursos disponibles.
- Regeneración limpia explícita de resultados existentes mediante el pipeline común.
- CLI, wrappers multiplataforma, ejecutable y ejecución programada.
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

## Traducción local offline

La release 1.6.0 incorpora un proveedor opcional español→inglés basado en CTranslate2 + SentencePiece. El modelo no se descarga automáticamente por defecto: debe prepararse explícitamente.

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

Después de preparar el modelo, puede seleccionarse con:

```dotenv
TRANSLATION_PROVIDER=local
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
```

El modelo y su revisión están fijados por el proyecto. La aplicación valida los ficheros principales por tamaño y SHA-256 y valida estructuralmente los metadatos requeridos antes de cargarlo. Consulte [`docs/LOCAL_TRANSLATION.md`](docs/LOCAL_TRANSLATION.md) y [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Wrappers locales

Los wrappers comparten un único dispatcher para conservar exactamente los argumentos recibidos en Windows y POSIX:

### Linux / macOS

```bash
./scripts/run_local.sh run --config ./config/app.toml
./scripts/run_local.sh regenerate --config ./config/app.toml --no-webm
```

### Windows

```powershell
.\scripts\run_local.bat run --config .\config\app.toml
.\scripts\run_local.bat regenerate --config .\config\app.toml --no-webm
```

`regenerate` elimina únicamente el subcomando del wrapper antes de invocar `src.regeneration`; no se reenvía como argumento adicional al parser Python.

## Regeneración completa

Cuando necesitas volver a generar un vídeo cuyo resultado ya existe utilizando **la implementación actual completa del pipeline**, utiliza la operación explícita `REGENERATE FROM ZERO`:

```bash
video-translation-regenerate
```

Los wrappers locales también exponen esta misma operación sin duplicarla:

```bash
./scripts/run_local.sh regenerate --config config/app.toml
```

En Windows:

```text
.\scripts\run_local.bat regenerate --config config\app.toml
```

La regeneración no es `resume` ni una recuperación selectiva. Localiza los resultados registrados, los aparta temporalmente mediante backup, fuerza el procesamiento desde la fuente a través de `MediaPipeline` y elimina los backups anteriores únicamente después de completar correctamente la regeneración. La fuente original se conserva. Si el procesamiento falla, los backups se restauran cuando el backend permite la operación de rename.

Consulta [`docs/REGENERATION.md`](docs/REGENERATION.md) para las garantías y limitaciones específicas de local, Google Drive y rclone.

## Naming de vídeos

El naming distingue explícitamente entre información lógica y representación física. El texto/contenido original se conserva; la representación física se genera mediante una política determinista y segura antes de crear carpetas o artefactos.

La nomenclatura física de referencia es:

```text
<curso_o_contenedor>x<nombre_sanitizado>
```

`x` es exclusivamente el separador de ámbito entre contenedor/curso y recurso. Dentro de cada bloque, `_` es el separador de palabras; no se utiliza `-` como separador de palabras. La estructura lógica no debe recuperarse buscando cualquier `x` dentro del nombre: debe conservarse en metadata/manifest.

La normalización física se aplica de forma centralizada en el límite de creación del recurso. Incluye, de forma determinista:

- espacios y separadores de palabras → `_`;
- eliminación de espacios iniciales/finales y separadores repetidos;
- eliminación/control de caracteres de filesystem (`\\ / : * ? " < > |`) y puntuación problemática, incluidos paréntesis, corchetes y comillas;
- conversión de enumeraciones como `1. Introducción` a `1_Introduccion` en la representación física;
- normalización Unicode y transliteración de diacríticos para nombres físicos (`ñ` → `n`, `á` → `a`, etc.);
- protección de nombres reservados de Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1`…`LPT9`);
- ajuste a los límites de componente/ruta del filesystem de destino;
- detección de colisiones antes de sobrescribir y uso de una estrategia determinista cuando el flujo necesita reservar un nombre.

La extracción ZIP aplica además validación de rutas absolutas/UNC, traversal, symlinks, nombres reservados y colisiones Unicode/case antes de escribir. El mismo contrato físico debe respetarse posteriormente en carpetas y artefactos generados (MP4/WebM/VTT), evitando que una entrada segura del ZIP produzca después un nombre físico inseguro.

La política se valida mediante casos funcionales representativos de las estructuras de nombres soportadas por el proyecto. Estos casos no constituyen una dependencia del runtime y cualquier regla adicional debe implementarse en la política, no mediante excepciones arbitrarias dispersas.

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

Cuando Whisper usa CUDA, el proyecto utiliza GPU para la inferencia y CPU para el trabajo auxiliar de CTranslate2; la paralelización adicional se realiza entre vídeos independientes cuando el presupuesto de recursos lo permite. No se presenta como una partición de una misma inferencia entre CPU y GPU.

Esta lógica forma parte del código central y no se duplica en los scripts de ejecución.

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

La CI además comprueba packaging, entry points, seguridad y dependencias en Linux, Windows y macOS para Python 3.11, 3.12 y 3.13. Consulta [`docs/CI_CD.md`](docs/CI_CD.md).

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
| [`docs/LOCAL_TRANSLATION.md`](docs/LOCAL_TRANSLATION.md) | Traducción local offline |
| [`docs/CUDA.md`](docs/CUDA.md) | Runtime NVIDIA/CUDA |
| [`docs/UNINSTALLATION.md`](docs/UNINSTALLATION.md) | Limpieza y desinstalación |

Los documentos históricos `PROJECT_GUIDE.md`, `VTT_REPAIR.md`, `UNATTENDED.md` y `VERSIONING.md` se mantienen por compatibilidad de navegación; los documentos anteriores son la referencia canónica para cada tema.

## Versionado

La release publicada actual es `1.5.1` (`v1.5.1`). La candidata de próxima release es **`1.6.0` (`v1.6.0`)** y no se considera publicada hasta que exista un tag/release verificable sobre el SHA resultante de `main`.

La release `1.5.1` corresponde al endurecimiento de extracción ZIP y componentes de filesystem multiplataforma. El tag `v1.5.1` apunta al commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

No se modifica el historial de releases anteriores.

## Seguridad y licencias

No versionar secretos, tokens ni claves. Los modelos, pesos y voces TTS pueden tener licencias diferentes de las librerías que los ejecutan. Antes de redistribuir el ejecutable o usarlo comercialmente debe revisarse la licencia concreta de cada componente.
