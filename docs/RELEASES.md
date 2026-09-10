# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

Una release agrupa un conjunto funcional coherente. Los tags publicados son inmutables.

## Releases publicadas

### 1.7.4 — Fix local translation shared vocabulary validation

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.4`.

**Publicado:** 8 de septiembre de 2026.

Corrige la validación de `shared_vocabulary.json` del modelo `Prukario/opus-mt-es-en-ct2-int8`. El artefacto real utiliza una raíz JSON de tipo array; la validación anterior exigía incorrectamente una raíz objeto. Se mantienen la validación estricta de `config.json` y `tokenizer_config.json`, los hashes/tamaños de los artefactos principales y la revisión fijada del modelo.

La release `v1.7.4` ya existe en GitHub y **no debe recrearse, mover su tag ni tratarse como candidata futura**.

### 1.7.3 — Local translation model metadata bootstrap

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.3`.

Distribuye `config.json` y `tokenizer_config.json` del modelo local fijado junto al paquete Python y conserva `shared_vocabulary.json`, `model.bin`, `source.spm` y `target.spm` como artefactos descargados y validados.

### 1.7.2 — Local Translation Model Download Fix

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.2`.

Corrige el cálculo del límite de descarga del modelo local y evita el `KeyError: 'model.bin'` provocado por la evaluación eager del fallback de `dict.get`.

### 1.7.1 — STT selective recovery compatibility

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.1`.

Corrige el contrato `clip_timestamps` de la recuperación selectiva de `faster-whisper`, utilizando intervalos numéricos `[start, end]`.

### 1.7.0 — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** `MINOR`.

**Tag publicado:** `v1.7.0`.

Consolida reprocessing/manifests, naming Unicode/filesystem, límites multiplataforma y el runtime de traducción local.

### 1.6.0 — Local Translation & GPU Runtime Hardening

**Tipo:** `MINOR`.

**Commit/tag publicado:** `a6cf0ee183a4802814fe0e061b4704e427166b85` / `v1.6.0`.

Introduce el proveedor local CTranslate2 + SentencePiece, gestión del modelo, runtime CUDA gestionado y recuperación STT configurable.

### 1.5.1 — ZIP Extraction & Cross-Platform Filesystem Hardening

**Tipo:** `PATCH`.

**Commit/tag publicado:** `06ee8d265b57214596f079f3bb426b9b27042b1e` / `v1.5.1`.

Endurece extracción ZIP, rutas absolutas/UNC, traversal, symlinks, nombres reservados de Windows y colisiones Unicode/case.

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR`.

**Commit/tag publicado:** `261f4b475f452b98880815f722aa8f8f43d28097` / `v1.5.0`.

Consolida wrappers multiplataforma, naming determinista, contexto externo de Whisper y packaging.

### 1.4.0 — Clean Video Regeneration & Release Hardening

**Tipo:** `MINOR`.

**Commit/tag publicado:** `ce1da6ea69a89f5a789c0670b200d6038f1a746d` / `v1.4.0`.

Introduce regeneración limpia mediante el pipeline común y endurece backup/restore y validación de release.

### 1.3.0 — Safe Resource-Aware Video Concurrency

**Tipo:** `MINOR`.

**Commit/tag publicado:** `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` / `v1.3.0`.

Introduce concurrencia adaptada a CPU/RAM/GPU.

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH`.

Elimina timestamps técnicos de descripciones y nombres generados.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH`.

Corrige la instalación de modelos TTS en Windows y unifica el bootstrap multiplataforma.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR`.

Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR`.

Introduce recuperación de VTT, regeneración selectiva y TTS sincronizado.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH`.

### 1.0.0 — Primera release estable

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.

## Próxima release — 1.8.0

### Posición en la línea de releases

**Tipo:** `MINOR`.

**Previous published release:** `v1.7.4`.

**Target tag:** `v1.8.0` — pendiente de validación final y publicación.

No se propone `1.7.5`: el alcance combinado de la migración reproducible a `uv` y la estabilización de Whisper con el nuevo fallback local MADLAD introduce funcionalidad compatible nueva y, por SemVer, corresponde a una release MINOR.

### Alcance funcional

- Separación del silencio VAD (`1500 ms`) y el silencio utilizado para separar subtítulos (`750 ms`).
- Recuperación de segmentos sospechosos sin `initial_prompt` ni contexto previo.
- Conservación de `clip_timestamps` numéricos.
- Sustitución del fallback local OPUS-MT por MADLAD-400 3B CT2 INT8 fijado.
- Tokenización SentencePiece compartida y prefijo `<2en>` para la traducción español→inglés.
- Presupuesto de instalación de 3.000.000.000 bytes, validación SHA-256 y descarga automática desactivada por defecto.
- Migración completa de desarrollo, CI, build y auditoría a `uv`, manteniendo instalación limpia del wheel con `pip`.

### CI y auditoría

La CI debe ejecutar `uv lock --check`, `uv sync --locked`, `uv pip check`, tests, packaging y auditoría de dependencias. Para `pip-audit`, el proyecto editable se elimina del entorno de auditoría antes de ejecutar:

```bash
uv run --locked --no-sync --group audit pip-audit --strict
```

Así se audita el grafo instalable de dependencias y no el paquete fuente local del propio repositorio.

### Validación

La candidata final debe completar CI y Release Gate sobre el SHA exacto final, con Linux, Windows y macOS y Python 3.11–3.13. También debe validarse el modelo MADLAD real en el hardware objetivo mediante el benchmark local.

### Trazabilidad y tag

`v1.7.4` ya está publicado y es inmutable. `v1.8.0` solo debe crearse después del merge de las PR correspondientes, sobre el SHA exacto de `main` que haya pasado CI y Release Gate.

## Historial anterior

Antes de la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
