# Changelog

## [1.5.2] — Local translation and runtime hardening

**Tipo:** PATCH — infraestructura opcional de traducción local, control reproducible de runtime y fallback sin servicios externos.

### Added

- Proveedor de traducción local autocontenido basado en CTranslate2 + SentencePiece.
- Modelo español→inglés OPUS-MT CTranslate2 INT8 fijado a una revisión inmutable.
- Gestión explícita del modelo bajo `tools/models/translation/`.
- Verificación de tamaño y SHA-256 de los ficheros principales del modelo.
- Descarga HTTPS a temporales con límite de tamaño, reemplazo atómico y reanudación mediante `.part` cuando el servidor admite Range.
- Script `scripts/manage_local_translation.py` para `status`, `download` y `cleanup`.
- Fallback de traducción local configurable sin dependencia de Ollama ni LM Studio.
- Control explícito de `faster-whisper` y CTranslate2 mediante rangos de versiones compatibles.
- Fallback de traducción local CUDA→CPU cuando el probe de CTranslate2 no permite utilizar CUDA.

### Changed

- La cadena de fallback predeterminada incluye el provider local antes de los proveedores remotos secundarios.
- La configuración permite seleccionar dispositivo y compute type del provider local.

### Security

- No se ejecutan binarios descargados como parte de la preparación del modelo.
- Los recursos locales se validan antes de cargarse y no se sustituyen por una descarga parcial.
- La descarga está restringida al origen HTTPS y revisión fijados.

### Documentation

- Actualizadas instalación, STT, traducción, providers y packaging para explicar CPU/GPU, modelo local, licencia, recursos y cleanup.

### Validation

- Añadidos tests para recurso ausente, hash incorrecto, aceptación de recursos verificados, cancelación sin confirmación y fallback CUDA→CPU.
- La validación completa sobre el SHA final queda pendiente de CI y del entorno real de ejecución; no se considera verificado ningún benchmark GPU/CPU hasta ejecutarlo.

## [1.5.0] — Multiplatform wrappers, reference naming and Whisper context

**Tipo:** MINOR — nuevas capacidades compatibles de ejecución multiplataforma, naming determinista basado en el árbol de referencia y configuración de contexto externo para Whisper.

### Added

- Dispatcher común para `run_local.sh` y `run_local.bat`, preservando exactamente los argumentos después de eliminar únicamente el subcomando del wrapper.
- Soporte coherente de `run` y `regenerate` mediante los entry points existentes y el `MediaPipeline` común.
- Política de naming basada en el par ZIP/vídeo extraído y validada contra el conjunto completo de ejemplos suministrado en `arbol_zips.txt`.
- `whisper_initial_prompt` puede seguir siendo un prompt literal o apuntar a `txt`, `md`, `csv` y `docx`.
- Soporte convencional de `palabras_contexto.<extensión>` y empaquetado del recurso de contexto.
- CI de tests sobre Linux, Windows y macOS para Python 3.11, 3.12 y 3.13.

### Whisper / hardware

- Se documenta explícitamente la estrategia real de GPU+CPU: CTranslate2 ejecuta la inferencia en CUDA cuando corresponde, mientras los hilos CPU realizan trabajo auxiliar y el pipeline paraleliza vídeos independientes dentro del presupuesto de CPU/RAM/VRAM.
- No se declara como soportada una partición de una misma inferencia Whisper entre CPU y GPU.
- Se conserva el fallback controlado CUDA → CPU existente.

### Security

- Los nombres derivados de archivos externos continúan tratándose como componentes de filesystem; la extracción ZIP mantiene las validaciones contra traversal y symlinks.
- Los archivos de contexto están limitados a 2 MiB y el lector DOCX rechaza DTD/entity declarations.

### Tests / validation

- Regresiones parametrizadas para todos los casos del archivo de referencia de naming.
- Tests para forwarding de wrappers y eliminación correcta de `regenerate`/`run`.
- Tests para contexto TXT, Markdown, CSV y DOCX.
- CI multiplataforma y multiversión ampliada.

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

### Packaging

- La wheel incluye explícitamente `config/*.toml`, incluido `config/app.toml`, para que la configuración predeterminada esté disponible después de instalar el paquete.
- La validación de packaging comprueba que la wheel contiene la configuración predeterminada y los cuatro console entry points publicados.

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
