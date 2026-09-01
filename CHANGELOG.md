# Changelog

## [1.4.2] — Regeneration CLI contract and help alignment

**Tipo:** MINOR — ampliación compatible del contrato de CLI de regeneración y documentación completa del help público.

### Added

- Regeneración acepta las opciones de `run` cuya semántica es válida para el `MediaPipeline` común: provider, source/target, normalización de nombres, concurrencia de vídeo, batching de traducción, configuración de Whisper, comportamiento de FFmpeg y selección de WebM.
- Regeneración reutiliza las acciones `argparse` reales de `run` y `_apply_run_overrides`, evitando un parser y una configuración paralelos.
- Se mantienen explícitamente como exclusivas de `run` las opciones `--scheduled`, `--dry-run`, `--no-retain-sources` y `--no-resume`, porque no son aplicables o contradicen la semántica de regeneración.
- El help de los comandos y subcomandos CLI se ha completado con tipos, choices, defaults, restricciones y descripción del comportamiento cuando corresponde.
- Se incorporan regresiones para las flags compartidas, help heredado, aliases `-h`/`--help`, exclusiones de regeneración, mutual exclusion de WebM y defaults.

### Documentation

- Actualizada la referencia `docs/CLI.md` con el contrato completo de `run` y la clasificación de flags de regeneración.
- Actualizada `docs/REGENERATION.md` con opciones compartidas, exclusiones, defaults, restricciones y garantías por proveedor.
- Actualizado el README para reflejar el contrato de CLI y los entry points disponibles.

### Validation

- Suite pytest y regresiones de CLI.
- Ruff y Ruff Security.
- Ruff format.
- `compileall`.
- `pip check`.
- `pip-audit`.
- Build y validación del wheel.
- Validación de entry points y CLI help.
- CI sobre Python 3.11, 3.12 y 3.13.

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH — correcciones compatibles y adaptación de los scripts de ejecución a los entry points existentes.

### Fixed

- Los wrappers locales exponen la regeneración limpia mediante la implementación existente `src.regeneration` / `video-translation-regenerate`.
- `scripts/run_local.sh` y `scripts/run_local.bat` no duplican regeneración, storage, rollback ni concurrencia; únicamente despachan al entry point existente.

### Validation

- Regresión del wrapper de regeneración.
- Suite pytest, Ruff, Ruff Security, Ruff format, compileall, pip check y pip-audit.
- Packaging y validación del wheel.
- E2E de entry point y wrapper de regeneración.
- CI sobre el SHA candidato final.

## [1.4.0] — Clean Video Regeneration and Release Hardening

**Tipo:** MINOR — nueva operación de regeneración limpia compatible con el pipeline existente, acompañada de endurecimiento de release, gobernanza y packaging/documentación.

### Added

- `video-translation-regenerate` como entry point para regenerar resultados de vídeo existentes desde la fuente original.
- Regeneración limpia basada en el `MediaPipeline` común, sin crear un pipeline audiovisual alternativo.
- Backup previo de resultados derivados y restauración ante fallo cuando el backend permite rename.
- Limpieza de backups únicamente después de una regeneración exitosa.
- Validación del entry point de regeneración en CI y packaging.
- Reglas de gobernanza del repositorio mediante `CONTRIBUTING.md`.

### Fixed / Hardened

- Se retira el workflow puntual de formateo que modificaba ramas; el formateo queda como comprobación de CI.
- Se alinea la metadata del paquete con `1.4.0` para la candidata de release.

### Validation status

La release publicada valida el contenido integrado en `main`. La aprobación definitiva de futuras releases requiere que el SHA candidato tenga una ejecución CI completa y satisfactoria y que los gates de seguridad, tests, packaging, documentación y versionado estén cerrados.

## [1.3.0] — Safe Resource-Aware Video Concurrency

**Tipo:** MINOR — nueva gestión adaptativa de concurrencia compatible hacia atrás.

### Added / Improved

- `max_parallel_videos = 0` activa selección automática de concurrencia basada en los recursos disponibles.
- El límite efectivo se calcula de forma conservadora a partir de CPU, RAM y GPU cuando CUDA está disponible.
- La resolución efectiva de dispositivo y configuración de Whisper se realiza antes de calcular la concurrencia.
- Los valores positivos de `max_parallel_videos` continúan siendo límites superiores y se recortan cuando superan la capacidad segura detectada.
- Se mantiene explícitamente el comportamiento de un único worker con `max_parallel_videos = 1`.
- La gestión de memoria GPU evita contar dos veces memoria compartida con el sistema.

### Fixed

- Alineada la versión declarada en `pyproject.toml` con el ciclo de releases del proyecto.

### Validation

- Regresiones para concurrencia AUTO.
- Regresiones para clamping por recursos.
- Regresión para single-worker.
- Suite pytest.
- Ruff lint, formato y seguridad.
- Compileall y packaging.
- Auditorías de dependencias y TTS.

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH — corrección compatible de la política de nombres.

### Fixed

- Evita que metadatos técnicos de fecha/hora procedentes de ZIP, carpetas extraídas o nombres de origen formen parte de la descripción del curso.
- Amplía la limpieza de formatos de fecha y datetime.
- Elimina timestamps técnicos antes de extraer números o descripciones de curso/lección.
- Evita incorporar timestamps a nombres de carpetas y archivos de salida.

### Validation

- Regresiones de nombres de curso/lección.
- Validación de limpieza de timestamps.
- Suite pytest.
- Ruff lint/formato/seguridad.
- Packaging y auditoría de dependencias.
