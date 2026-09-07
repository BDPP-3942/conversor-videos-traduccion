# Changelog

## [1.6.1] — STT selective recovery compatibility

**Tipo:** PATCH — corrección compatible hacia atrás de la recuperación selectiva de segmentos sospechosos de STT.

### Fixed

- Corregido el contrato de `clip_timestamps` usado por la recuperación selectiva de `faster-whisper`: los intervalos se envían como valores temporales numéricos `[start, end]` en lugar de diccionarios.
- Añadidas pruebas de regresión que verifican el argumento recibido por `model.transcribe(...)`, la transcripción normal y la integración del resultado recuperado.

### Validation

- Validación CI multiplataforma y Release Gate sobre el SHA final de la corrección.
- Compatibilidad verificada con `faster-whisper>=1.2.1,<1.3`.

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
