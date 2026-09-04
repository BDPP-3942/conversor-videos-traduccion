# Changelog

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
- Instalación interactiva y explícita de las bibliotecas NVIDIA runtime cuando faltan.
- Fallback CPU conservador cuando CUDA no puede validarse.
- Fallback de traducción local configurable sin dependencia de Ollama ni LM Studio.
- Control explícito de `faster-whisper` y CTranslate2 mediante rangos de versiones compatibles.
- Recuperación configurable de segmentos STT sospechosos mediante rondas de recuperación limitadas.

### Changed

- La cadena de fallback predeterminada incluye el provider local antes de los proveedores remotos secundarios.
- `WHISPER_DEVICE=auto` ya no interpreta la mera presencia de `nvidia-smi` como capacidad CUDA válida.
- La configuración permite seleccionar dispositivo y compute type del provider local mediante `LOCAL_TRANSLATION_*`.
- Un CUDA Toolkit global no se modifica ni se desinstala automáticamente; el runtime gestionado puede coexistir con él.
- La recuperación STT conserva el contexto en el primer intento y puede realizar un intento adicional sin contexto dentro de cada ronda configurada.

### Security

- No se ejecutan binarios descargados como parte de la preparación del modelo.
- Los recursos locales se validan antes de cargarse y no se sustituyen por una descarga parcial.
- La descarga está restringida al origen HTTPS y revisión fijados.
- La instalación CUDA gestionada no modifica el driver NVIDIA ni un CUDA Toolkit global.
- La limpieza CUDA elimina exclusivamente `tools/cuda/`; la limpieza del modelo elimina exclusivamente su directorio gestionado.
- Se mantienen las protecciones ZIP/filesystem de `1.5.1`.

### Documentation

- Actualizadas instalación, STT, traducción, providers, packaging y releases para explicar CPU/GPU, modelo local, licencia, recursos y cleanup.
- Añadidas `docs/CUDA.md` y `docs/UNINSTALLATION.md`.
- Actualizada la documentación de release para reflejar la clasificación MINOR de `1.6.0`.

### Validation

- Suite pytest completa validada en CI.
- CI multiplataforma validada sobre Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- Ruff lint, security y format validados.
- `compileall`, packaging, instalación limpia de wheel, `pip check`, entry points y auditorías de dependencias validados.
- Release Gate validado sobre el SHA final pre-merge.
- Tests de modelo local cubren recurso ausente, hash incorrecto, metadatos inválidos, preparación sin confirmación y descarga reanudable.
- Tests de CUDA cubren ausencia de NVIDIA, runtime incompleto y capacidad CTranslate2 verificada.
- Tests de STT cubren recuperación deshabilitada, rondas configurables y parada temprana ante candidato saludable.
- Tests de ZIP/filesystem cubren traversal, rutas absolutas/UNC, symlinks, nombres reservados y colisiones.

No se declara ningún benchmark GPU/CPU ni prueba A/B de un MP4 externo que no haya sido ejecutado y registrado.

## [1.5.1] — ZIP extraction and cross-platform filesystem hardening

**Tipo:** PATCH — correcciones compatibles de seguridad e integridad de archivos.

### Fixed

- La extracción ZIP rechaza rutas absolutas POSIX/Windows, rutas UNC y traversal mediante separadores `/` o `\\`.
- Se rechazan componentes de ruta reservados por Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1`...`COM9`, `LPT1`...`LPT9`).
- Se detectan colisiones de rutas antes de escribir cuando difieren únicamente por case o normalización Unicode.
- Las entradas ZIP duplicadas ya no pueden sobrescribir silenciosamente un archivo previamente extraído.
- Se detectan colisiones del directorio de extracción antes de reutilizar una ubicación existente.
- Los componentes de filesystem generados por la aplicación se protegen frente a nombres reservados de Windows.

### Security

- La validación de miembros ZIP se realiza antes de la escritura y exige que los destinos permanezcan dentro del workspace de extracción.
- Las entradas simbólicas ZIP siguen siendo rechazadas.

### Tests / validation

- Añadidos tests de regresión para rutas absolutas Windows, UNC, traversal con backslashes, nombres reservados, colisiones Unicode/case y entradas duplicadas.
- Añadidos tests para componentes de salida reservados por Windows.

## [1.5.0] — Multiplatform Whisper, Context & Packaging

**Tipo:** MINOR — nuevas capacidades compatibles de ejecución multiplataforma, naming determinista basado en reglas de normalización y configuración de contexto externo para Whisper.

### Added

- Dispatcher común para `run_local.sh` y `run_local.bat`, preservando exactamente los argumentos después de eliminar únicamente el subcomando del wrapper.
- Soporte coherente de `run` y `regenerate` mediante los entry points existentes y el `MediaPipeline` común.
- Política de naming basada en el par ZIP/vídeo extraído y validada mediante casos representativos de las estructuras soportadas.
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

- Regresiones parametrizadas para los casos representativos de naming.
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
- Se alinea la versión declarada en `pyproject.toml` con `1.4.0` para la candidata de release.

### Validation status

La release publicada valida el contenido integrado en `main`. La aprobación definitiva de futuras releases requiere que el SHA candidato tenga CI completa y satisfactoria y que los gates de seguridad, tests, packaging, documentación y versionado estén cerrados.

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
