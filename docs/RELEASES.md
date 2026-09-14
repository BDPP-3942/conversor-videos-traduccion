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
| --- | ---: |
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación VTT e integración TTS en el pipeline común | `1.1.0` |
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
| Recuperación STT refinada y soporte de dos modelos locales fijados, incluyendo MADLAD-400 3B y OPUS-MT | `1.8.0` |
| Bootstrap de uv gestionado por el proyecto y preparación opcional de traducción local | `1.8.1` |
| Corrección del recurso MADLAD, tokenizer, fixtures y diagnóstico de descarga | `1.8.2` |
| Resolución consistente de uv gestionado por el proyecto en wrappers POSIX/Windows | `1.8.3` (candidata) |

## Releases publicadas

### 1.8.2 — MADLAD model download and Hugging Face revision fix

**Tipo:** `PATCH`.

**Tag publicado:** `v1.8.2`.

**Commit de referencia:** `0165f7fdd000c0f29c8a022fa26a452afc55111c`.

Corrige la revisión fijada de MADLAD-400 3B CT2 INT8, utiliza el tokenizer real `spiece.model`, mantiene la validación de integridad y diferencia diagnósticos `404` de `401/403` en Hugging Face.

### 1.8.1 — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** `PATCH`.

**Tag publicado:** `v1.8.1`.

**Commit de referencia:** `a4a5b9143d6fe6d61b9780220394189ef88c25ec`.

Introduce el bootstrap gestionado de uv sin instalación global obligatoria y la preparación opt-in del modelo local de traducción.

### 1.8.0 — Whisper Recovery & Local Translation

**Tipo:** `MINOR`.

**Tag publicado:** `v1.8.0`.

Consolida la recuperación selectiva de Whisper, separa el silencio VAD del split de subtítulos, incorpora MADLAD-400 3B CT2 INT8 como modelo local predeterminado manteniendo OPUS-MT como alternativa ligera, y refuerza la validación de ambos modelos.

### 1.7.4 — uv and Local Translation Validation

**Tipo:** `PATCH`.

**Tag publicado:** `v1.7.4`.

Consolida la validación de `shared_vocabulary.json` y la migración reproducible de desarrollo, CI, build y auditoría a `uv`.

### 1.7.3 — Local Translation Model Metadata Bootstrap

**Tipo:** `PATCH`.

Bootstrap de metadatos JSON del modelo local.

### 1.7.2 — Local Translation Model Download Fix

**Tipo:** `PATCH`.

Corrige el gestor de descarga del modelo local y la preparación del flujo proveedor-modelo.

### 1.7.1 — STT Selective Recovery Compatibility

**Tipo:** `PATCH`.

Corrige el contrato `clip_timestamps` usado por la recuperación selectiva de `faster-whisper`.

### 1.7.0 — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** `MINOR`.

Consolida reprocesado, manifests, naming Unicode/filesystem y runtime de traducción local.

### 1.6.0 — Local Translation & GPU Runtime Hardening

**Tipo:** `MINOR`.

Introduce traducción local opcional, runtime GPU gestionado y recuperación STT configurable.

### 1.5.1 — ZIP Extraction & Cross-Platform Filesystem Hardening

**Tipo:** `PATCH`.

Endurece la extracción ZIP, traversal, rutas absolutas/UNC, symlinks, nombres reservados y colisiones Unicode/case.

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR`.

Introduce wrappers multiplataforma, contexto externo de Whisper y packaging reproducible.

### 1.4.2 — Regeneration CLI Contract and Help Alignment

**Tipo:** `MINOR`.

Amplía y documenta el contrato CLI de regeneración.

### 1.4.1 — Corrective Script Integration

**Tipo:** `PATCH`.

Integra la regeneración en wrappers sin duplicar lógica del pipeline.

### 1.4.0 — Clean Video Regeneration and Release Hardening

**Tipo:** `MINOR`.

Introduce regeneración limpia, backup/restauración y endurecimiento de release.

### 1.3.0 — Safe Resource-Aware Video Concurrency

**Tipo:** `MINOR`.

Introduce concurrencia adaptativa basada en CPU/RAM/GPU.

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH`.

Elimina timestamps técnicos de nombres y resultados.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH`.

Corrige la instalación multiplataforma de recursos TTS.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR`.

Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR`.

Introduce recuperación de VTT, regeneración selectiva y TTS sincronizado.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH`.

Añade y corrige la documentación inicial de instalación.

### 1.0.0 — Primera release estable

**Tipo:** primera release de producto de esta línea.

## Candidata 1.8.3

### Posición en la línea de releases

**Tipo:** `PATCH`.

**Previous published release:** `1.8.2`.

**Target tag:** `v1.8.3`, pendiente de validación final y publicación sobre el SHA exacto resultante de `main`.

### Alcance

- Resolver `uv` de forma compartida en POSIX y Windows.
- Priorizar siempre la copia gestionada en `tools/uv/` frente a `PATH`.
- Corregir los wrappers y scripts de build que seguían suponiendo una instalación global de uv.
- Mantener la prioridad de ejecutables empaquetados y el fallback Python de unattended.
- Añadir regresiones específicas de resolución y contratos de wrappers.

### Integridad histórica

`v1.8.0`, `v1.8.1` y `v1.8.2` son releases publicadas. No se consideran candidatas, no se sustituyen por `1.8.3` y sus entradas históricas no deben eliminarse ni degradarse. `1.8.3` es la única candidata activa.

### Validación

La candidata debe completar CI y Release Gate sobre su SHA exacto, incluyendo Linux, Windows y macOS con Python 3.11–3.13, tests, lint/format, audits, packaging, instalación limpia, `pip check`, entry points y validación del lockfile.

### Política de tags

`v1.8.3` solo debe crearse sobre el SHA exacto validado por Release Gate y resultante de `main`. No se debe crear ni mover el tag desde la rama de la PR.

## Historial anterior

Antes de la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
