# Changelog

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
