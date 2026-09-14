# Changelog

## [1.8.3] — Release candidate

**Estado:** CANDIDATA — corrección multiplataforma del mecanismo de resolución de `uv`, pendiente de CI/Release Gate, merge y publicación del tag `v1.8.3`.

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

- Actualizados `RELEASE_CANDIDATE.md`, `RELEASE_SCOPE.md`, `docs/UV_MIGRATION.md`, `docs/VERSIONING.md`, `docs/RELEASES.md`, `docs/PROJECT.md` y `docs/CI_CD.md`.
- La documentación de instalación mantiene el contrato de bootstrap automático y ahora documenta explícitamente la resolución compartida de los consumidores.

### Compatibility

- PATCH compatible con la línea `1.8.x`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.2] — Release candidate superseded

**Estado:** CANDIDATA PREVIA — supersedida por `1.8.3` antes de publicación.

- Corrección de la revisión fijada de MADLAD-400 3B CT2 INT8.
- Corrección del tokenizer a `spiece.model`.
- Validación de tamaño/SHA-256 y diagnóstico diferenciado de errores 404 frente a 401/403.
- Corrección de fixtures y regresiones de local translation.

## [1.8.1] — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** PATCH.

- Bootstrap de uv gestionado por el proyecto sin requerir instalación global.
- Prioridad de `tools/uv/` frente a uv de `PATH`.
- Bootstrap equivalente en macOS/Linux y Windows.
- Opción `--local-translation` para preparar el modelo local de forma opt-in.

## [1.8.0] — Whisper Recovery & Local Translation

**Tipo:** MINOR.

- Recuperación selectiva de Whisper refinada y separación de umbrales VAD/subtítulos.
- MADLAD-400 3B CT2 INT8 como modelo local predeterminado, con OPUS-MT como alternativa.
- Validación reforzada de modelos, contexto Whisper y defaults TTS/WebM.
- Base reproducible de desarrollo, CI, build y auditoría con uv.

## [1.7.4] — Local Translation Validation

**Tipo:** PATCH.

- Corrección de validación de `shared_vocabulary.json`.
- Migración reproducible de desarrollo/CI/build/auditoría a uv.

## [1.7.3] — Local Translation Metadata Bootstrap

**Tipo:** PATCH.

- Metadatos JSON del modelo local incluidos en el paquete y validados durante la preparación.

## [1.7.2] — Local Translation Download Fix

**Tipo:** PATCH.

- Corrección del gestor de descarga y preparación del modelo local.
- Regresiones de descarga, inicialización y traducción.

## [1.7.1] — STT Selective Recovery Compatibility

**Tipo:** PATCH.

- Corrección del contrato `clip_timestamps` de `faster-whisper` para recuperación selectiva.

## [1.7.0] — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** MINOR.

- Reprocessing y manifests.
- Naming Unicode/filesystem determinista y endurecimiento multiplataforma.
- Runtime de traducción local CTranslate2 + SentencePiece.

## [1.6.0] — Local Translation & GPU Runtime Hardening

**Tipo:** MINOR.

- Traducción local opcional, runtime CUDA gestionado, diagnóstico GPU/CPU y recuperación STT configurable.

## [1.5.1] — ZIP Extraction and Filesystem Hardening

**Tipo:** PATCH.

- Protección ZIP frente a traversal, rutas absolutas/UNC, symlinks, nombres reservados y colisiones Unicode/case.

## [1.5.0] — Multiplatform Wrappers, Whisper Context & Packaging

**Tipo:** MINOR.

- Wrappers multiplataforma, contexto Whisper, naming determinista y packaging.

## [1.4.2] — Regeneration CLI Contract

**Tipo:** PATCH/MINOR histórica.

- Contrato CLI de regeneración y help alineados con el pipeline común.

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH.

- Integración de regeneración en wrappers sin duplicar lógica del pipeline.

## [1.4.0] — Clean Video Regeneration and Release Hardening

**Tipo:** MINOR.

- Regeneración limpia, backup/restauración y endurecimiento de release, gobernanza y packaging.

## [1.3.0] — Safe Resource-Aware Video Concurrency

**Tipo:** MINOR.

- Concurrencia automática basada en CPU/RAM/GPU con límites conservadores.

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH.

- Eliminación de timestamps técnicos de nombres de curso/lección y resultados.

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH.

- Corrección de instalación de assets TTS, especialmente en Windows.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR.

- Naming descriptivo determinista y bootstrap de assets Kokoro.

## [1.1.0] — VTT Repair and TTS Integration

**Tipo:** MINOR.

- Recuperación de VTT inválidos, regeneración controlada y TTS sincronizado en el pipeline común.

## [1.0.1] — Installation and Maintenance Documentation

**Tipo:** PATCH.

- Guía de instalación y navegación documental inicial.

## [1.0.0] — First Stable Release

Primera release estable del producto.
