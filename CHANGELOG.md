# Changelog

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH — correcciones compatibles y adaptación de los scripts de ejecución a los entry points existentes.

### Fixed

- Los wrappers locales exponen la regeneración limpia mediante el entry point existente `src.regeneration` / `video-translation-regenerate`.
- La ejecución de regeneración desde `scripts/run_local.sh` y `scripts/run_local.bat` reutiliza exactamente la implementación común de regeneración; no crea un pipeline alternativo.
- Se mantiene la concurrencia segura existente y su clamping en el core, sin duplicar su cálculo en `scripts/`.

### Validation

- Regresión de integración del wrapper de regeneración.
- Suite pytest.
- Ruff lint y Ruff Security.
- Ruff format, compileall, pip check y pip-audit.
- Packaging y validación del wheel.
- E2E sobre entry point y wrapper de regeneración.
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

La release publicada valida el contenido integrado en `main`. La aprobación de futuras releases requiere que el SHA candidato tenga una ejecución CI completa y satisfactoria y que los gates de seguridad, tests, packaging, documentación y versionado estén cerrados.

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
