# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

Una release agrupa un conjunto funcional coherente. Los tags publicados son inmutables.

## Funcionalidades con evidencia de introducción

| Funcionalidad | Primera versión verificada |
|---|---:|
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación de VTT e integración TTS en el pipeline común | `1.1.0` |
| Naming descriptivo y bootstrap de assets TTS | `1.2.0` |
| Corrección multiplataforma de assets TTS | `1.2.1` |
| Limpieza de timestamps técnicos en naming | `1.2.2` |
| Concurrencia adaptada a CPU/RAM/GPU | `1.3.0` |
| Regeneración limpia explícita de resultados | `1.4.0` |
| Integración de regeneración en wrappers locales | `1.4.1` |
| Contrato CLI ampliado y documentación completa de regeneración | `1.4.2` |
| Wrappers multiplataforma, naming de referencia y contexto externo de Whisper | `1.5.0` |
| Endurecimiento ZIP/filesystem multiplataforma | `1.5.1` |
| Traducción local opcional, recuperación STT configurable y endurecimiento GPU/runtime | `1.6.0` |
| Reprocessing/manifests, consolidación de naming Unicode/filesystem y mejoras del runtime de traducción local | `1.7.0` |
| Corrección del contrato `clip_timestamps` en la recuperación selectiva de STT con `faster-whisper` | `1.7.1` |
| Corrección de descarga del modelo local y validación del flujo proveedor-modelo | `1.7.2` |
| Bootstrap de metadatos JSON del modelo local | `1.7.3` |
| Validación de `shared_vocabulary.json` y migración reproducible de desarrollo/CI/build a `uv` | `1.7.4` |
| Recuperación STT refinada y soporte de dos modelos locales fijados, incluyendo MADLAD-400 3B y OPUS-MT | `1.8.0` (candidata) |

## Releases publicadas

### 1.7.4 — uv and Local Translation Validation

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.4`.

Consolida la validación de `shared_vocabulary.json` y la migración reproducible de desarrollo, CI, build y auditoría a `uv`, conservando la compatibilidad del wheel con `pip` y los metadatos del modelo local.

### 1.7.2 — Local Translation Model Download Fix

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.2`.

Corrige el cálculo del límite de descarga del modelo local y evita el `KeyError: 'model.bin'` provocado por la evaluación eager del fallback de `dict.get`. Mantiene la validación de integridad y añade regresiones para el flujo proveedor-modelo.

### 1.7.0 — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** `MINOR`.

**Tag publicado:** `v1.7.0`.

Consolida el reprocesado y la persistencia de manifests, refuerza el almacenamiento local multiplataforma, consolida el naming determinista y la normalización Unicode, endurece los límites reales de filesystem y consolida el proveedor de traducción local y su runtime.

### 1.6.0 — Local Translation & GPU Runtime Hardening

**Tipo:** `MINOR`.

**Commit/tag publicado:** `a6cf0ee183a4802814fe0e061b4704e427166b85` / `v1.6.0`.

- Traducción local opcional español→inglés basada en CTranslate2 + SentencePiece.
- Modelo local fijado y validado mediante tamaño y SHA-256.
- Descarga reanudable, validación estructural y reemplazo atómico de recursos.
- Runtime NVIDIA gestionado para cuBLAS CUDA 12 y cuDNN 9 CUDA 12.
- Detección de capacidad CUDA real mediante CTranslate2 y fallback CPU conservador.
- Recuperación configurable de segmentos STT sospechosos mediante rondas limitadas.
- Endurecimiento ZIP/filesystem heredado de `1.5.1`.

### 1.5.1 — ZIP Extraction & Cross-Platform Filesystem Hardening

**Tipo:** `PATCH`.

**Commit/tag publicado:** `06ee8d265b57214596f079f3bb426b9b27042b1e` / `v1.5.1`.

- Protección contra rutas absolutas, UNC y traversal multiplataforma.
- Protección contra symlinks y nombres reservados de Windows.
- Detección de colisiones por case y normalización Unicode.
- Prevención de sobrescritura silenciosa de entradas ZIP duplicadas.
- Sanitización de componentes de filesystem generados por la aplicación.
- Release publicada el 3 de septiembre de 2026.

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR`.

**Commit/tag publicado:** `261f4b475f452b98880815f722aa8f8f43d28097` / `v1.5.0`.

- Dispatcher común para `run_local.sh` y `run_local.bat`.
- Naming determinista y validación multiplataforma.
- `whisper_initial_prompt` mediante literal y archivos de contexto.
- Estrategia documentada CPU/GPU con CTranslate2.
- CI sobre Linux, Windows y macOS para Python 3.11–3.13.

### 1.4.0 — Clean Video Regeneration & Release Hardening

**Tipo:** `MINOR`.

**Commit/tag publicado:** `ce1da6ea69a89f5a789c0670b200d6038f1a746d` / `v1.4.0`.

- Regeneración limpia mediante el `MediaPipeline` común.
- Contrato público `StorageProvider` para backup, restore y eliminación.
- Concurrencia segura y validación de release.

### 1.3.0 — Safe Resource-Aware Video Concurrency

**Tipo:** `MINOR`.

**Commit/tag publicado:** `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` / `v1.3.0`.

- `max_parallel_videos = 0` significa AUTO.
- Cálculo conservador según CPU, RAM y GPU.
- Los valores positivos actúan como límites superiores sujetos al techo seguro.

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH`.

- Elimina timestamps técnicos de descripciones y nombres generados.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH`.

- Corrige la instalación de modelos TTS en Windows y unifica el bootstrap multiplataforma.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR`.

- Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR`.

- Recuperación de VTT, regeneración selectiva y TTS sincronizado desde VTT validado.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH`.

- Añade y corrige la guía documental de instalación.

### 1.0.0 — Primera release estable

**Tipo:** primera release de producto de esta línea.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.


## Candidata 1.8.0

### Posición en la línea de releases

**Tipo:** `MINOR`.

**Previous published release:** `1.7.4`.

**Target tag:** `v1.8.0`, pendiente de validación final, merge de PR #45 y publicación sobre el SHA exacto resultante de `main`.

### Alcance

- Separación de la duración de silencio VAD de la división de subtítulos (`2000 ms` frente a `1000 ms`).
- Recuperación de segmentos STT sospechosos sin prompt inicial ni contexto de texto previo.
- Conservación de `clip_timestamps` numérico durante la recuperación selectiva.
- Conservación de **dos modelos locales**: MADLAD-400 3B CT2 INT8 como opción predeterminada y OPUS-MT CT2 INT8 como alternativa ligera compatible.
- Validación de integridad, revisiones fijadas, tokenización específica de cada modelo y configuración explícita del modelo seleccionado.
- Voz TTS predeterminada `am_michael` y generación WebM desactivada por defecto, con activación explícita mediante las opciones de CLI correspondientes.
- Regresiones de tests para MADLAD, selección explícita de OPUS-MT y aislamiento de configuración frente a overrides del entorno.
- Base reproducible de desarrollo/CI/build/auditoría con `uv` ya integrada mediante PR #42 en el baseline `1.7.4`.

### Validación

La candidata final debe completar CI y Release Gate sobre su SHA exacto, incluyendo Linux, Windows y macOS con Python 3.11–3.13, tests, lint/format, audits, packaging, instalación limpia, `pip check`, entry points y validación del lockfile.

La descarga del modelo MADLAD (~2.95 GB) no forma parte del CI normal; su benchmark real debe ejecutarse explícitamente en el hardware objetivo. OPUS-MT conserva una vía de preparación independiente para entornos con poco espacio.

### Política de tags

`v1.8.0` solo debe crearse sobre el SHA exacto validado por Release Gate y resultante del merge a `main`. No se debe crear ni mover el tag desde la rama de la PR.

## Historial anterior

Antes de la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.