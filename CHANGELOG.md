# Changelog

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

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH — corrección compatible de instalación de recursos TTS.

### Fixed

- Corrige la instalación de modelos TTS en Windows ante `PermissionError: [WinError 32]`.
- Cierra los archivos temporales antes de moverlos a su destino.
- Hace consistente el bootstrap de assets TTS entre Windows, Linux y macOS.
- Evita que descargas TTS fallidas dejen archivos temporales bloqueados.

### Compatibility

No cambia el formato de modelos TTS, las variables de configuración, los formatos de salida ni el pipeline TTS.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR — funcionalidad compatible de naming y bootstrap TTS.

### Added / Improved

- Convención de nombres `[course_number]_[course_description]x[lesson_number]_[lesson_description]` cuando la información está disponible.
- Mejor detección de números/descripciones de curso y lección y soporte para resultados ya procesados.
- Bootstrap TTS capaz de preparar los assets Kokoro bajo `tools/tts/` cuando TTS está habilitado.
- Validación del host de las descargas de modelos TTS.
- Detección de resultados previamente procesados para evitar reprocesado audiovisual innecesario.

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — funcionalidad compatible para recuperar resultados existentes y ejecutar TTS desde el flujo común.

### Added

- Recuperación automática de VTT originales y traducidos con timestamps inválidos o sintaxis WebVTT no válida.
- Regeneración de STT sobre el vídeo normal existente cuando el VTT original no puede validarse.
- Regeneración de traducción cuando el VTT traducido es inválido o cuando el STT tuvo que reconstruirse.
- Integración de la reparación de VTT antes de TTS.
- Validación final de timestamps después de la segmentación STT por silencios.
- Generación TTS sincronizada desde el VTT traducido validado.
- Reutilización de artefactos TTS existentes cuando siguen siendo válidos.
- Copias de seguridad de VTT antes de sustituir artefactos defectuosos.

### Fixed

- Los cues STT con `start >= end` ya no se propagan como subtítulos utilizables.
- Un VTT histórico inválido ya no bloquea la recuperación.
- Un VTT traducido inválido ya no obliga a repetir STT cuando la transcripción original sigue siendo válida.
- `TTS_ENABLED=true` activa el postprocesado TTS en el pipeline común.
- Los VTT inválidos no se utilizan como entrada de síntesis.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación.

### Fixed

- Añadida la guía de instalación referenciada desde `README.md`.
- Corregidos enlaces del índice de documentación.
