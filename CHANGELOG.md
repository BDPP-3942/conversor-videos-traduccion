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
- La detección local de ZIP con `input_min_age_seconds=0` ya no depende de una diferencia de reloj del filesystem; el valor cero significa explícitamente que no se exige antigüedad.
- La normalización física de nombres conserva Unicode en NFC en lugar de transliterarlo a ASCII, evitando pérdida silenciosa de información y colisiones creadas por transliteración.
- Las escrituras de manifests usan temporales únicos en el mismo directorio y publicación mediante `os.replace`, evitando colisiones entre escritores.

### Security

- No se ejecutan binarios descargados como parte de la preparación del modelo.
- Los recursos locales se validan antes de cargarse y no se sustituyen por una descarga parcial.
- La descarga está restringida al origen HTTPS y revisión fijados.
- La instalación CUDA gestionada no modifica el driver NVIDIA ni un CUDA Toolkit global.
- La limpieza CUDA elimina exclusivamente `tools/cuda/`; la limpieza del modelo elimina exclusivamente su directorio gestionado.
- Se mantienen las protecciones ZIP/filesystem de `1.5.1`.
- La frontera de nombres físicos conserva Unicode y aplica únicamente transformaciones necesarias para seguridad del filesystem.

### Documentation

- Actualizadas instalación, STT, traducción, providers, packaging y releases para explicar CPU/GPU, modelo local, licencia, recursos y cleanup.
- Añadidas `docs/CUDA.md` y `docs/UNINSTALLATION.md`.
- Actualizada la documentación de release para reflejar la clasificación MINOR de `1.6.0`.
- Documentado el contrato Unicode NFC y su cobertura en tests.

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
