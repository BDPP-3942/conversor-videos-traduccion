# Changelog

## [1.8.3] — Release candidate

**Estado:** CANDIDATA — corrección multiplataforma del mecanismo de resolución de `uv`, pendiente de CI/Release Gate, merge y publicación del tag `v1.8.3`.

**Baseline:** `1.8.2` candidate state. This patch keeps the existing `uv` bootstrap architecture and fixes the consumers that incorrectly required a global `uv` on `PATH` after setup had already installed the project-managed binary under `tools/uv/`.

### Fixed

- Añadido un resolvedor POSIX compartido que prioriza `tools/uv/uv` y usa `uv` de `PATH` como fallback.
- Añadido el resolvedor equivalente para Windows, priorizando `tools\\uv\\uv.exe` antes de `PATH`.
- Corregidos `run_local`, `run_unattended`, `setup_rclone`, `setup_google` y los scripts de build para usar el ejecutable resuelto, en macOS/Linux y Windows.
- Conservada la prioridad de ejecutables empaquetados en los wrappers desatendidos y el fallback directo al Python del entorno cuando `uv` no está disponible.
- No se requiere instalar `uv` globalmente ni modificar los perfiles de shell del usuario.

### Tests / CI

- Añadida cobertura de regresión para la prioridad de `tools/uv/` sobre `PATH`.
- Añadidas comprobaciones de contrato para los wrappers POSIX y Windows y para los scripts de build/setup afectados.
- La suite de regresión verifica que los wrappers no vuelvan a depender de `command -v uv`/`where uv.exe` como precondición global.

### Documentation

- Actualizada la documentación de migración, versionado, release history y release candidate para describir el resolvedor compartido y el caso de uso sin `uv` global.

### Compatibility

- Release PATCH compatible sobre la línea `1.8.x`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.2] — Release candidate

**Estado:** CANDIDATA — pendiente de CI/Release Gate verde, merge a `main` y publicación del tag `v1.8.2`.

**Baseline publicado:** `v1.8.1`. Esta release recoge exclusivamente la corrección posterior al problema de descarga del modelo MADLAD detectado tras `1.8.1`.

### Fixed

- Corregida la revisión fijada de MADLAD-400 3B CT2 INT8 a `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Corregido el nombre del tokenizer: el artefacto real es `spiece.model`, no `sentencepiece.model`.
- Conservada la validación de tamaño y SHA-256 de los artefactos gestionados.
- Mejorado el diagnóstico de descargas de Hugging Face para distinguir un `404` de archivo/revisión inexistente de los errores de autenticación/autorización `401/403`.
- Corregidos los fixtures de tests de MADLAD para que los tamaños declarados coincidan con los bytes escritos.
- Alineados los metadatos de aplicación, packaging y documentación con la release `1.8.2`.

### Tests / CI

- Añadidas/regresadas pruebas para la revisión fijada, `spiece.model`, integridad, prefijo de destino MADLAD y diagnóstico de `404`.
- Mantiene cobertura independiente para OPUS-MT y su revisión fijada.
- La candidata requiere suite completa, `uv lock --check`, lint/format, packaging, auditoría y Release Gate antes de publicación.

### Compatibility

- Es una release PATCH compatible sobre `1.8.1`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.
- La corrección se limita al recurso MADLAD, su validación, diagnóstico y documentación asociada.

## [1.8.1] — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** PATCH — release publicada posterior a `1.8.0` para mejorar el bootstrap del entorno de desarrollo y la preparación opcional del modelo de traducción local.

**Tag publicado:** `v1.8.1`.

**Commit de referencia:** `a4a5b9143d6fe6d61b9780220394189ef88c25ec`.

### Bootstrap automático de uv

- Los scripts de creación del entorno ya no requieren que `uv` esté instalado previamente en el sistema.
- Se reutiliza primero una copia gestionada por el proyecto en `tools/uv/`.
- Si no existe, se utiliza `uv` disponible en `PATH`.
- Si tampoco existe, el instalador oficial de uv crea automáticamente una copia local bajo `tools/uv/`.
- El bootstrap local no modifica los perfiles de shell del usuario.
- Se mantiene el comportamiento equivalente en macOS/Linux y Windows.
- El binario local de uv no se versiona en Git.

### Instalación opcional del modelo local

- Añadida la opción `--local-translation` a los scripts de setup para preparar durante el mismo proceso el modelo local de traducción fijado por el proyecto.
