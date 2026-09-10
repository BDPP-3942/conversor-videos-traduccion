# Changelog

## [1.8.0] — Whisper recovery and dual local translation models

**Tipo:** MINOR — nueva funcionalidad compatible para estabilizar la recuperación selectiva de STT y conservar dos modelos locales de traducción offline.

### Added / Improved

- Separada la duración de silencio del VAD de la división de subtítulos de Whisper (`1500 ms` frente a `750 ms`).
- La recuperación de segmentos STT sospechosos puede reintentar sin el prompt inicial ni el contexto de texto previo, evitando amplificar alucinaciones del prompt de contexto.
- Se conserva `clip_timestamps` con intervalos numéricos `[start, end]` durante la recuperación selectiva.
- Se conservan dos modelos locales CTranslate2: MADLAD-400 3B INT8 como opción predeterminada y OPUS-MT INT8 como alternativa ligera compatible.
- Cada modelo mantiene repositorio, revisión, artefactos, tokenización, validación de integridad y configuración seleccionable de forma independiente.
- MADLAD utiliza SentencePiece compartido y el prefijo de destino `<2en>`; OPUS-MT conserva `source.spm` y `target.spm`.
- Se mantiene la descarga explícita y el fallback conservador a CPU cuando CUDA no puede validarse.
- Se completa la migración reproducible de desarrollo/CI/build/auditoría a `uv`.

### Compatibility

- `v1.7.4` permanece publicada e inmutable.
- Se conservan las correcciones de `1.7.1`, `1.7.2` y `1.7.3`, incluidos `clip_timestamps`, la descarga del modelo OPUS-MT y sus metadatos JSON empaquetados.
- No se introduce una arquitectura alternativa de procesamiento ni se elimina la vía de traducción local OPUS-MT.

### Validation

- CI debe validar Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- Se mantienen las regresiones E2E de pipeline/regeneración y las adaptaciones multiplataforma de los subprocessos.
- La descarga/benchmark real de MADLAD queda como validación explícita en el hardware objetivo por su tamaño aproximado de 2.95 GB.

## [1.7.4] — Local translation shared vocabulary validation

**Tipo:** PATCH — corrección compatible del validador de metadatos del modelo de traducción local.

### Fixed

- Corregida la validación de `shared_vocabulary.json` del modelo CTranslate2 local.
- `shared_vocabulary.json` puede tener una raíz JSON de tipo array, que es la estructura real del artefacto fijado `Prukario/opus-mt-es-en-ct2-int8@ad91ad1697ea1761111ff4c179400796d085b347`.
- Se mantiene la validación estricta de raíz objeto y claves obligatorias para `config.json` y `tokenizer_config.json`.
- La descarga desde cero del modelo ya puede completar la validación y activar el directorio gestionado del modelo local.

### Tests

- Añadida regresión específica para aceptar un `shared_vocabulary.json` con raíz array.
- Añadida regresión para rechazar `shared_vocabulary.json` con JSON inválido.
- Actualizados los fixtures de descarga y carga del proveedor para representar la estructura real del vocabulario compartido.
- CI multiplataforma validada sobre Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.

### Compatibility

- No cambian el modelo ni la revisión fijados.
- No cambian los hashes ni tamaños esperados de `model.bin`, `source.spm` y `target.spm`.
- No cambia la configuración pública del proveedor de traducción local.
- Se conserva íntegramente la corrección de metadatos empaquetados introducida en `1.7.3`.

## [1.7.3] — Local translation model metadata bootstrap

**Tipo:** PATCH — corrección compatible para garantizar la disponibilidad de los metadatos JSON requeridos por el runtime de traducción local.

### Fixed

- Añadidos al paquete los metadatos `config.json` y `tokenizer_config.json` correspondientes exactamente a la revisión fijada `Prukario/opus-mt-es-en-ct2-int8@ad91ad1697ea1761111ff4c179400796d085b347`.
- La preparación del modelo ya no depende de una descarga independiente desde Hugging Face para esos dos JSON pequeños.
- El gestor instala los metadatos empaquetados en el directorio final del modelo antes de validar y activar el runtime.
- `shared_vocabulary.json` continúa descargándose y validándose como artefacto del modelo, ya que forma parte del contenido generado por CTranslate2 y no se duplica innecesariamente dentro del paquete Python.

### Tests

- Añadida una regresión que verifica que los metadatos JSON empaquetados están disponibles.
- Ajustada la regresión de descarga para comprobar explícitamente que los ficheros descargados son `model.bin`, `source.spm`, `target.spm` y `shared_vocabulary.json`, mientras que los dos metadatos pequeños proceden del paquete.
- Se mantiene la prueba de inicialización del proveedor y traducción mediante CTranslate2 + SentencePiece.

### Packaging

- Añadido el subpaquete `config.local_translation_model` al artefacto Python para que los JSON necesarios estén presentes también en instalaciones empaquetadas.

### Compatibility

- No cambian el modelo/revisión fijados, la configuración pública ni el contrato de dependencias.
- Se conserva la corrección de descarga de `1.7.2` y la corrección `clip_timestamps` de `1.7.1`.

## [1.7.2] — Local translation model download fix

**Tipo:** PATCH — corrección compatible del gestor de preparación del modelo de traducción local.

### Fixed

- Corregido el cálculo del límite de descarga de los ficheros del modelo local.
- Evitada la evaluación eager del fallback de `dict.get` que provocaba `KeyError: 'model.bin'` aunque `model.bin` estuviera correctamente definido en `MODEL_FILES`.
- La preparación vuelve a poder recorrer los tres ficheros principales (`model.bin`, `source.spm`, `target.spm`) y los metadatos JSON antes de validar y activar el modelo.

### Tests

- Añadida regresión que ejercita la descarga gestionada de todos los ficheros del modelo.
- Añadida regresión que prepara el modelo y comprueba la inicialización del proveedor y una llamada de traducción a través de CTranslate2 + SentencePiece.
- Se mantiene el benchmark real `scripts/benchmark_local_translation.py` como validación funcional del modelo fijado en el hardware objetivo.

### Documentation

- Actualizadas las instrucciones de preparación del modelo local y la explicación del fallo corregido.
- Actualizada la documentación de release y versionado para `1.7.2`.

### Compatibility

- No cambian el modelo/revisión fijados, la configuración pública, el pipeline audiovisual ni el contrato de dependencias.
- Se conserva la corrección `clip_timestamps` de `1.7.1`.

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
- Mejorada la persistencia y recuperación del estado de procesamiento mediante manifests, incluyendo escritura atómica y detección explícita de manifests corruptos o ilegibles.
- Reforzado el comportamiento multiplataforma del almacenamiento local para evitar condiciones de carrera relacionadas con la antigüedad de archivos y timestamps del filesystem.
- Consolidada la generación determinista de nombres de salida para vídeos, cursos y lecciones.
- Normalización Unicode estable mediante descomposición canónica NFD, eliminación de marcas diacríticas y recomposición NFC.
- Los nombres generados mantienen letras y números Unicode válidos, evitando transliteraciones arbitrarias y garantizando un comportamiento estable entre representaciones NFC/NFD.
- Reforzada la compatibilidad con las restricciones reales de los sistemas de archivos de Windows, Linux y macOS.
- Consolidada la protección frente a colisiones de nombres por mayúsculas/minúsculas y normalización Unicode.
- Mejorada la gestión de nombres y rutas que superan los límites del filesystem, incluyendo componentes Unicode cuyo tamaño debe calcularse en bytes UTF-8.

### Translation

- Consolidado el proveedor opcional de traducción local basado en CTranslate2 + SentencePiece.
- Mejorada la gestión del modelo local y su validación antes de ser utilizado.
- Añadida gestión configurable de la autenticación necesaria para descargar modelos privados o restringidos de Hugging Face.
- Los modelos públicos pueden prepararse sin necesidad de proporcionar credenciales.
- Mantenida la validación de integridad de los artefactos del modelo mediante tamaño y SHA-256.
- Consolidada la selección de dispositivo y `compute_type` para traducción local, manteniendo fallback conservador a CPU cuando GPU/CUDA no puede utilizarse correctamente.

### Filesystem & ZIP

- Consolidado el endurecimiento de extracción ZIP introducido en `v1.5.1`.
- Mantenida la protección frente a traversal mediante `/` y `\\`, rutas absolutas POSIX/Windows, rutas UNC, nombres reservados de Windows, entradas ZIP duplicadas, colisiones por case-folding, colisiones por normalización Unicode y entradas simbólicas.
- Preservada la estructura de directorios de los ZIP anidados y reforzada la normalización NFC de nombres de miembros y contenedores.

### Tests & Validation

- Ampliadas las regresiones de naming para nombres Unicode compuestos y descompuestos.
- Añadidas comprobaciones para eliminar diacríticos mediante normalización canónica sin transliteraciones selectivas.
- Ampliadas las pruebas de reprocessing, manifests, backups, restauración ante errores y validación de subtítulos.
- Mantenida la matriz multiplataforma de Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- Validación mediante Ruff, Ruff Security, Ruff format, `compileall`, `pip check`, packaging, wheel e instalación limpia.
- Mantenidas las auditorías de dependencias y las validaciones del Release Gate.

### Compatibility

Esta es una release minor compatible con la arquitectura existente. No introduce una arquitectura alternativa de procesamiento.

### Release

**Version:** `1.7.0`

**Previous release:** `1.6.0`

**Release type:** MINOR

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
- Estrategia documentada CPU/GPU con CTranslate2.
- Packaging reproducible del ejecutable y recursos de configuración.

### Changed

- Endurecida la validación de argumentos de los wrappers locales.
- Mejorada la resolución de FFmpeg para entornos empaquetados y de desarrollo.

### Tests / validation

- Añadidos tests de wrappers y de integración con el pipeline común.
- Validación multiplataforma sobre Linux, Windows y macOS.

## [1.4.2] — Regeneration CLI and documentation

**Tipo:** MINOR — ampliación compatible del contrato CLI de regeneración y de su documentación.

### Added

- Contrato CLI de regeneración explícito y documentado.
- Validación de argumentos y salida estructurada para regeneración.

## [1.4.1] — Cross-platform regeneration integration

**Tipo:** PATCH — integración compatible de regeneración en wrappers multiplataforma.

### Fixed

- Los wrappers locales invocan el entry point de regeneración sin duplicar el subcomando.

## [1.4.0] — Clean video regeneration

**Tipo:** MINOR — regeneración limpia de resultados existentes mediante el pipeline común.

### Added

- Regeneración desde cero con backup y restore ante errores.
- Integración de regeneración con manifests y estado de procesamiento.

## [1.3.0] — Resource-aware video concurrency

**Tipo:** MINOR — concurrencia adaptada a CPU, RAM y GPU.

### Added

- `max_parallel_videos = 0` para selección automática.
- Techo seguro de concurrencia basado en recursos disponibles.

## [1.2.2] — Naming timestamp cleanup

**Tipo:** PATCH — limpieza de timestamps técnicos en nombres generados.

## [1.2.1] — TTS installation fix

**Tipo:** PATCH — corrección multiplataforma de instalación de assets TTS.

## [1.2.0] — Naming and TTS improvements

**Tipo:** MINOR — naming descriptivo y bootstrap de assets Kokoro.

## [1.1.0] — VTT repair and synchronized TTS

**Tipo:** MINOR — recuperación de VTT y TTS sincronizado a partir de VTT validado.

## [1.0.1] — Installation documentation

**Tipo:** PATCH — instalación y documentación inicial de mantenimiento.

## [1.0.0] — First stable release

**Tipo:** primera release estable de la línea de producto `1.x`.
