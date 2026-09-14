# Changelog

## [1.8.2] — Release candidate

**Estado:** CANDIDATA — pendiente de CI/Release Gate verde, merge a `main` y publicación del tag `v1.8.2`.

**Baseline publicado:** `v1.8.0`. La preparación de `1.8.1` no llegó a publicarse y queda supersedida por esta corrección necesaria para hacer reproducible la descarga del modelo MADLAD.

### Fixed

- Corregida la revisión fijada de MADLAD-400 3B CT2 INT8 a `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Corregido el nombre del tokenizer: el artefacto real es `spiece.model`, no `sentencepiece.model`.
- Conservada la validación de tamaño y SHA-256 de los artefactos gestionados.
- Mejorado el diagnóstico de descargas de Hugging Face para no presentar un `404` de archivo/revisión como un problema de autenticación; `401/403` sí se diagnostican como posibles problemas de credenciales.
- Corregidos los fixtures de tests de MADLAD para que los tamaños declarados coincidan con los bytes escritos.
- Alineados los metadatos de aplicación, packaging y documentación con la release `1.8.2`.

### Tests / CI

- Añadidas/regresadas pruebas para la revisión fijada, `spiece.model`, integridad, prefijo de destino MADLAD y diagnóstico de `404`.
- Mantiene cobertura independiente para OPUS-MT.
- La candidata requiere suite completa, `uv lock --check`, lint/format, packaging, auditoría y Release Gate antes de publicación.

## [1.8.0] — Release candidate

**Estado:** CANDIDATA — pendiente de merge de PR #45, validación final de CI/Release Gate y publicación del tag `v1.8.0`.

**Baseline publicado:** `v1.7.4`. PR #42 (migración reproducible a `uv`) ya forma parte de `main` y del baseline `1.7.4`; esta candidata registra las mejoras finales de PR #45 sobre ese estado.

### Scope

- Refinada la recuperación selectiva de segmentos sospechosos de Whisper, con reintento sin prompt inicial ni contexto de texto previo.
- Separados el silencio VAD (`2000 ms`) y la división de subtítulos (`1000 ms`).
- Conservado el contrato numérico de `clip_timestamps` durante la recuperación.
- Incorporado MADLAD-400 3B CT2 INT8 como modelo local predeterminado, manteniendo OPUS-MT como alternativa ligera.
- Añadida validación específica de integridad, tokenización, revisiones fijadas y presupuesto de instalación del modelo MADLAD.
- Reforzadas las regresiones de modelos locales, selección explícita de OPUS-MT y aislamiento de los tests de configuración frente a overrides del entorno.
- Actualizado el contexto de Whisper para vocabulario de Tai Chi.
- Cambiada la voz TTS predeterminada a `am_michael` y desactivada la generación WebM por defecto.
- Conservada la base de desarrollo, CI, build y auditoría con `uv` introducida por PR #42.

### Validation

La candidata requiere suite completa de tests, CI multiplataforma, Release Gate, packaging y validación del lockfile sobre el SHA exacto final.

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
