# Changelog

## [1.7.1] — STT selective recovery compatibility

**Tipo:** PATCH — corrección compatible sobre la release `1.7.0` para la recuperación selectiva de segmentos sospechosos de STT.

### Fixed

- Corregido el contrato de `clip_timestamps` usado por la recuperación selectiva de `faster-whisper`: los intervalos se envían como valores temporales numéricos `[start, end]` en lugar de diccionarios.
- Añadidas pruebas de regresión que verifican el argumento recibido por `model.transcribe(...)`, la transcripción normal y la integración del resultado recuperado.

### Compatibility

- La revisión toma `v1.7.0` como baseline funcional inmediato y conserva sus capacidades de reprocessing/manifests, naming Unicode/filesystem y runtime de traducción local.
- Compatibilidad verificada con `faster-whisper>=1.2.1,<1.3`.

### Validation

- CI multiplataforma y Release Gate deben validarse sobre el SHA final de esta candidata.

## [1.7.0] — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** MINOR — nuevas capacidades compatibles para reprocesado, manifests, naming Unicode/filesystem y consolidación del runtime de traducción local.

### Added / Improved

- Consolidado el procesamiento de reintentos y reprocesado de vídeos mediante `reprocess-subtitles`, incluyendo `stt_only`, `translate_only`, `full` y `reprocess_all`.
- Mejorada la persistencia y recuperación del estado mediante manifests con escritura atómica y detección explícita de manifests corruptos o ilegibles.
- Reforzado el almacenamiento local multiplataforma frente a condiciones de carrera relacionadas con antigüedad de archivos y timestamps del filesystem.
- Consolidada la generación determinista de nombres para vídeos, cursos y lecciones.
- Normalización Unicode estable mediante NFD, eliminación de marcas diacríticas y recomposición NFC.
- Reforzada la compatibilidad con límites reales de filesystem de Windows, Linux y macOS.
- Consolidada la protección frente a colisiones por case-folding y normalización Unicode.
- Mejorada la gestión de nombres y rutas que superan los límites del filesystem, incluyendo componentes Unicode cuyo tamaño debe calcularse en bytes UTF-8.
- Consolidado el proveedor opcional de traducción local basado en CTranslate2 + SentencePiece y su validación.
- Añadida gestión configurable de autenticación para modelos privados o restringidos de Hugging Face.
- Consolidada la selección de dispositivo y `compute_type` para traducción local con fallback conservador a CPU.
- Consolidado el endurecimiento ZIP/filesystem heredado de `1.5.1`.

### Validation

- Regresiones de naming Unicode, reprocessing, manifests, backups, restauración y subtítulos.
- CI multiplataforma con Python 3.11, 3.12 y 3.13.
- Ruff, Ruff Security, Ruff format, `compileall`, `pip check`, packaging, wheel e instalación limpia.
- Auditorías de dependencias y Release Gate.

### Release

`v1.7.0` es la release publicada inmediatamente anterior a `1.7.1`.

## [1.6.0] — Local Translation & GPU Runtime Hardening

**Tipo:** MINOR — funcionalidad nueva compatible hacia atrás para traducción local opcional, runtime GPU reproducible y recuperación STT configurable.

### Added

- Proveedor de traducción local basado en CTranslate2 + SentencePiece para español→inglés.
- Modelo español→inglés OPUS-MT CTranslate2 INT8 fijado a la revisión `ad91ad1697ea1761111ff4c179400796d085b347`.
- Gestión explícita del modelo bajo `tools/models/translation/`.
- Verificación de tamaño y SHA-256 de los ficheros principales del modelo.
- Descarga HTTPS a temporales con límite de tamaño, reemplazo atómico y reanudación mediante `.part` cuando el servidor admite Range.
- Script `scripts/manage_local_translation.py` para `status`, `download` y `cleanup`.
- Gestión de runtime NVIDIA bajo `tools/cuda/` para cuBLAS CUDA 12 y cuDNN 9 CUDA 12.
- Diagnóstico de NVIDIA/CUDA/CTranslate2 antes de seleccionar GPU para Whisper o traducción local.
- Fallback CPU conservador cuando CUDA no puede validarse.
- Recuperación configurable de segmentos STT sospechosos mediante rondas de recuperación limitadas.

### Validation

- Suite pytest completa, CI multiplataforma, lint/security/format, compileall, packaging, instalación limpia, `pip check` y auditorías.
- Tests de modelo local, CUDA, STT y ZIP/filesystem.

## [1.5.1] — ZIP extraction and cross-platform filesystem hardening

**Tipo:** PATCH — correcciones compatibles de seguridad e integridad de archivos.

### Fixed

- La extracción ZIP rechaza rutas absolutas POSIX/Windows, rutas UNC y traversal mediante separadores `/` o `\\`.
- Se rechazan componentes de ruta reservados por Windows.
- Se detectan colisiones de rutas por case o normalización Unicode.
- Las entradas ZIP duplicadas ya no pueden sobrescribir silenciosamente un archivo previamente extraído.
- Se rechazan entradas simbólicas ZIP.

### Tests / validation

- Regresiones para rutas Windows/UNC, traversal, nombres reservados, colisiones Unicode/case y entradas duplicadas.

## [1.5.0] — Multiplatform Whisper, Context & Packaging

**Tipo:** MINOR — nuevas capacidades compatibles de ejecución multiplataforma, naming determinista y configuración de contexto externo para Whisper.

### Added

- Dispatcher común para `run_local.sh` y `run_local.bat`.
- Soporte coherente de `run` y `regenerate` mediante el `MediaPipeline` común.
- Política de naming basada en el par ZIP/vídeo extraído.
- `whisper_initial_prompt` como literal o contexto desde `txt`, `md`, `csv` y `docx`.
- CI sobre Linux, Windows y macOS para Python 3.11, 3.12 y 3.13.

### Whisper / hardware

- Estrategia documentada de GPU+CPU sin declarar partición de una misma inferencia Whisper entre CPU y GPU.
- Fallback controlado CUDA → CPU.

## [1.4.2] — Regeneration CLI contract and help alignment

**Tipo:** MINOR — ampliación compatible del contrato de CLI de regeneración y documentación del help público.

### Added

- Regeneración acepta las opciones de `run` válidas para el `MediaPipeline` común.
- Regeneración reutiliza las acciones `argparse` reales de `run` y `_apply_run_overrides`.
- El help de los comandos y subcomandos CLI se completa con tipos, choices, defaults y restricciones.

### Packaging

- La wheel incluye explícitamente `config/*.toml`, incluido `config/app.toml`.

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH — correcciones compatibles y adaptación de los scripts de ejecución a los entry points existentes.

### Fixed

- Los wrappers locales exponen la regeneración mediante `src.regeneration` / `video-translation-regenerate`.

## [1.4.0] — Clean Video Regeneration and Release Hardening

**Tipo:** MINOR — nueva operación de regeneración limpia compatible con el pipeline existente y endurecimiento de release, gobernanza y packaging.

### Added

- `video-translation-regenerate`.
- Regeneración limpia basada en el `MediaPipeline` común.
- Backup previo y restauración ante fallo cuando el backend permite rename.
- Validación del entry point de regeneración en CI y packaging.

## [1.3.0] — Safe Resource-Aware Video Concurrency

**Tipo:** MINOR — nueva gestión adaptativa de concurrencia compatible hacia atrás.

### Added / Improved

- `max_parallel_videos = 0` activa selección automática de concurrencia basada en recursos.
- Cálculo conservador a partir de CPU, RAM y GPU cuando CUDA está disponible.

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH — corrección compatible de la política de nombres.

### Fixed

- Evita que metadatos técnicos de fecha/hora formen parte de la descripción del curso o nombres de salida.

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH — corrección compatible de instalación de recursos TTS.

### Fixed

- Corrige la instalación de modelos TTS en Windows ante `PermissionError: [WinError 32]`.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR — funcionalidad compatible de naming y bootstrap TTS.

### Added / Improved

- Convención de nombres `[course_number]_[course_description]x[lesson_number]_[lesson_description]`.
- Bootstrap TTS de assets Kokoro.
- Detección de resultados previamente procesados.

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — funcionalidad compatible para recuperar resultados existentes y ejecutar TTS desde el flujo común.

### Added

- Recuperación automática de VTT originales y traducidos con timestamps inválidos.
- Regeneración de STT sobre el vídeo normal existente cuando el VTT original no puede validarse.
- Regeneración de traducción cuando el VTT traducido es inválido.
- Integración de la reparación de VTT antes de TTS.
- Generación TTS sincronizada desde el VTT traducido validado.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación.

### Fixed

- Añadida la guía de instalación referenciada desde `README.md`.
- Corregidos enlaces del índice de documentación.
