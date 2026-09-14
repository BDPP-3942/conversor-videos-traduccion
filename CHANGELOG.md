# Changelog

## [1.8.3] — Release candidate

**Estado:** CANDIDATA — corrección multiplataforma del mecanismo de resolución de `uv`, pendiente de CI/Release Gate y publicación del tag `v1.8.3`.

**Baseline publicado:** `v1.8.2`. Esta release añade exclusivamente la corrección de resolución de `uv` en los consumidores del bootstrap gestionado por el proyecto.

**Nota de alcance:** la aplicación de escritorio y su infraestructura de empaquetado implementadas en la rama de trabajo son funcionalidad nueva y no forman parte de la release PATCH `1.8.3`. Si se conserva esta capacidad en `main`, deberá publicarse en la siguiente release MINOR (actualmente `1.9.0`) con la actualización completa de metadatos y `uv.lock` exigida por `docs/VERSIONING.md`.

### Fixed

- Añadido un resolvedor POSIX compartido que prioriza `tools/uv/uv` y usa `uv` de `PATH` como fallback.
- Añadido el resolvedor Windows equivalente, que prioriza `tools\\uv\\uv.exe` antes de `PATH`.
- Corregidos `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*` y los scripts de build para consumir el ejecutable resuelto.
- Conservada la prioridad de ejecutables empaquetados en los wrappers unattended y el fallback directo a `.venv` Python cuando uv no está disponible.
- Eliminada la dependencia accidental de una instalación global de uv para ejecutar un checkout correctamente preparado por `setup_env.*`.

### Tests / CI

- Añadida `tests/test_uv_resolution_contract.py` con cobertura de los contratos POSIX y Windows.
- Verificada la precedencia de `tools/uv/` sobre `PATH`.
- Verificado que los wrappers y builds no vuelvan a exigir `command -v uv` o `where uv.exe` como precondición global.
- Conservada la matriz CI Linux/Windows/macOS y Python 3.11/3.12/3.13.

### Documentation

- Añadida la documentación específica de la resolución compartida de `uv` sin eliminar el historial de releases anteriores.
- Documentado el límite de versión que impide publicar la nueva aplicación de escritorio dentro de `1.8.3`.

### Compatibility

- PATCH compatible con la línea `1.8.x`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.2] — MADLAD model download and Hugging Face revision fix

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.2`.

**Commit/tag de referencia:** `0165f7fdd000c0f29c8a022fa26a452afc55111c` / `v1.8.2`.

### Fixed

- Corregida la revisión fijada de MADLAD-400 3B CT2 INT8 a `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Corregido el nombre del tokenizer: el artefacto real es `spiece.model`, no `sentencepiece.model`.
- Conservada la validación de tamaño y SHA-256 de los artefactos gestionados.
- Mejorado el diagnóstico de descargas de Hugging Face para distinguir un `404` de archivo/revisión inexistente de los errores de autenticación/autorización `401/403`.
- Corregidos los fixtures de tests de MADLAD para que los tamaños declarados coincidan con los bytes escritos.
- Alineados los metadatos de aplicación, packaging y documentación con la release `1.8.2`.

### Tests / CI

- Añadidas/regresadas pruebas para la revisión fijada, `spiece.model`, integridad, prefijo de destino MADLAD y diagnóstico de `404`.
- Mantenida cobertura independiente para OPUS-MT y su revisión fijada.
- Release Gate validado antes de publicar `v1.8.2`.

### Compatibility

- Release PATCH compatible sobre `1.8.1`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.
- La corrección se limita al recurso MADLAD, su validación, diagnóstico y documentación asociada.

## [1.8.1] — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.1`.

**Commit/tag de referencia:** `a4a5b9143d6fe6d61b9780220394189ef88c25ec` / `v1.8.1`.

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
- La descarga continúa siendo opt-in porque MADLAD-400 3B ocupa aproximadamente 2.95 GB.
- Se conserva la vía independiente `uv run python scripts/manage_local_translation.py download` para diferir la descarga.
- Se mantienen los comandos de `status` y benchmark del modelo local.

### Versionado y documentación

- Proyecto y configuración actualizados a `1.8.1`.
- `uv.lock` sincronizado con la nueva versión.
- Actualizadas las instrucciones de instalación, migración y uso de uv y el README.
- Añadidas regresiones para los contratos de los scripts de instalación.

### Compatibility

No se modifican el pipeline de procesamiento audiovisual, los contratos de almacenamiento, los formatos de entrada/salida, los modelos locales y sus revisiones fijadas, la cadena de proveedores de traducción, el runtime CUDA/NVIDIA ni la interfaz existente de `manage_local_translation.py`.

### Validation

- CI multiplataforma sobre Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- pytest, Ruff lint/format, comprobaciones de seguridad y `compileall`.
- `uv lock --check` y `uv pip check`.
- Auditorías de dependencias, packaging, construcción de distributions e instalación limpia del wheel.
- Release Gate validado antes de publicar `v1.8.1`.

## [1.8.0] — Whisper Recovery & Local Translation

**Tipo:** MINOR — release publicada.

**Estado:** PUBLICADA — tag `v1.8.0`.

### Scope

- Refinada la recuperación selectiva de segmentos sospechosos de Whisper, con reintento sin prompt inicial ni contexto de texto previo.
- Separados el silencio VAD (`2000 ms`) y la división de subtítulos (`1000 ms`).
- Conservado el contrato numérico de `clip_timestamps` durante la recuperación.
- Incorporado MADLAD-400 3B CT2 INT8 como modelo local predeterminado, manteniendo OPUS-MT como alternativa ligera.
- Añadida validación específica de integridad, tokenización, revisiones fijadas y presupuesto de instalación del modelo MADLAD.
- Reforzadas las regresiones de modelos locales, selección explícita de OPUS-MT y aislamiento de los tests de configuración frente a overrides del entorno.
- Actualizado el contexto de Whisper para vocabulario de Tai Chi.
