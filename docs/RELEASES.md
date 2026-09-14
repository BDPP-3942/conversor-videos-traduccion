# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`). Los tags publicados son inmutables.

## Funcionalidades con evidencia de introducción

| Funcionalidad | Primera versión verificada |
| --- | ---: |
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación VTT e integración TTS en el pipeline común | `1.1.0` |
| Naming descriptivo y bootstrap de assets TTS | `1.2.0` |
| Corrección multiplataforma de assets TTS | `1.2.1` |
| Limpieza de timestamps técnicos en naming | `1.2.2` |
| Concurrencia adaptada a CPU/RAM/GPU | `1.3.0` |
| Regeneración limpia explícita de resultados | `1.4.0` |
| Integración de regeneración en wrappers locales | `1.4.1` |
| Contrato CLI ampliado y documentación de regeneración | `1.4.2` |
| Wrappers multiplataforma, naming de referencia y contexto externo de Whisper | `1.5.0` |
| Endurecimiento ZIP/filesystem multiplataforma | `1.5.1` |
| Traducción local opcional, recuperación STT configurable y endurecimiento GPU/runtime | `1.6.0` |
| Reprocessing/manifests, naming Unicode/filesystem y runtime de traducción local | `1.7.0` |
| Corrección de recuperación selectiva STT | `1.7.1` |
| Corrección de descarga del modelo local | `1.7.2` |
| Bootstrap de metadatos JSON del modelo local | `1.7.3` |
| Validación de `shared_vocabulary.json` y migración reproducible a uv | `1.7.4` |
| Recuperación STT refinada y modelos locales fijados, incluyendo MADLAD y OPUS-MT | `1.8.0` |
| Corrección del recurso MADLAD y tokenizer | `1.8.2` (candidata previa) |
| Resolución consistente de uv gestionado por el proyecto en wrappers POSIX/Windows | `1.8.3` (candidata) |

## Release candidata actual

### 1.8.3 — Project-managed uv wrapper resolution

**Tipo:** `PATCH`.

**Estado:** candidata; pendiente de CI, Release Gate, merge y publicación del tag `v1.8.3`.

Esta release corrige la incoherencia entre el bootstrap de `uv` y los consumidores del ejecutable. `setup_env.*` ya podía instalar `uv` en `tools/uv/`, pero varios wrappers seguían buscando únicamente `uv`/`uv.exe` en `PATH`.

La implementación añade resolvedores compartidos:

- `scripts/lib/resolve_uv.sh` para POSIX.
- `scripts/lib/resolve_uv.bat` para Windows.

Ambos priorizan el ejecutable gestionado por el proyecto y usan `PATH` como fallback. Los scripts `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*` y los builds consumen ahora ese resolvedor.

La regresión se cubre en `tests/test_uv_resolution_contract.py` y verifica tanto la prioridad como la ausencia de una dependencia global obligatoria.

### Validación requerida

- pytest completo.
- Ruff lint/security/format y `compileall`.
- `uv lock --check`, `uv sync --locked` y `uv pip check`.
- Packaging y wheel.
- Auditorías.
- CI Linux/Windows/macOS con Python 3.11/3.12/3.13.
- Ejecución de wrappers con copia gestionada de uv y sin uv global en PATH.

## Releases publicadas

### 1.8.0 — Whisper Recovery & Local Translation

**Tipo:** `MINOR`.

**Tag publicado:** `v1.8.0`.

Consolida recuperación selectiva de Whisper, separación de umbrales VAD/subtítulos y modelos locales fijados.

### 1.7.4 — uv and Local Translation Validation

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.4`.

Consolida la validación de `shared_vocabulary.json` y la migración reproducible de desarrollo, CI, build y auditoría a `uv`.

Las releases anteriores permanecen documentadas en `CHANGELOG.md` y forman parte de la historia inmutable del proyecto.
