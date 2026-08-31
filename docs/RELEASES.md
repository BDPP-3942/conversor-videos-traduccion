# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La versión del proyecto no debe incrementarse por cada commit de formato o CI. Una release agrupa un conjunto funcional coherente.

## Funcionalidades con evidencia de introducción

La siguiente tabla solo asigna una versión cuando existe evidencia explícita en el historial de releases/changelog. Los cambios posteriores a la última release publicada se identifican como tales y no se les asigna una versión que todavía no existe.

| Funcionalidad | Primera versión verificada |
|---|---:|
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS sincronizado, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación de VTT e integración TTS en el pipeline común | `1.1.0` |
| Naming descriptivo/más resistente a colisiones y bootstrap de assets TTS | `1.2.0` |
| Corrección de instalación de assets TTS en Windows y consistencia multiplataforma | `1.2.1` |
| Limpieza de timestamps técnicos en naming | `1.2.2` |
| **Concurrencia de vídeo adaptada a recursos (CPU/RAM/GPU)** | **Posterior a `1.2.2` — PR #20** |

No se infieren versiones de introducción a partir de nombres de archivos, commits aislados o documentación histórica cuando el historial de releases no lo acredita.

## Releases publicadas verificadas

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH`.

Publicado el 28 de agosto de 2026.

- Evita incorporar metadatos de fecha/hora de ZIP, carpetas extraídas o nombres de origen en la descripción del curso.
- Amplía la limpieza de formatos de fecha y datetime antes de extraer números/descripciones de curso y lección.
- Mantiene la convención `[course_number]_[course_description]x[lesson_number]_[lesson_description]` cuando la información está disponible.
- Incluye regresiones de naming, limpieza de timestamps y las validaciones habituales de CI.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH`.

Publicado el 28 de agosto de 2026.

- Corrige la instalación de modelos TTS en Windows cuando un archivo temporal estaba todavía abierto (`WinError 32`).
- Cierra correctamente los archivos temporales antes de moverlos a su ubicación final.
- Hace consistente la instalación de recursos TTS entre Windows, Linux y macOS.
- Mantiene la reutilización de modelos existentes y los paths/configuración de TTS.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR`.

Publicado el 28 de agosto de 2026.

- Introduce la convención de nombres más descriptiva y resistente a colisiones para curso/lección.
- Mejora la detección de información de curso y lección y la migración de resultados existentes.
- Completa el bootstrap de TTS para preparar los assets Kokoro cuando TTS está habilitado.
- Valida explícitamente los hosts de descarga de recursos TTS.
- Permite completar artefactos TTS faltantes en resultados existentes.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR`.

- Recuperación de VTT originales/traducidos inválidos o ausentes.
- Regeneración selectiva de STT o traducción sin regenerar el vídeo normal.
- Validación final de timestamps después de segmentación STT.
- Integración de TTS en el pipeline común.
- Reutilización de TTS válido y backups de VTT antes de reemplazo.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH`.

- Añade la guía de instalación.
- Corrige la navegación documental del README.
- Documenta dependencias opcionales, FFmpeg, TTS, almacenamiento cloud, ejecución programada y actualización.

### 1.0.0 — Primera release estable

**Tipo:** primera release de producto de esta línea.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.

Incluye el pipeline audiovisual, FFmpeg, Whisper/faster-whisper, VTT y traducción con fallback, almacenamiento local/Google Drive/rclone, manifests/resume, deduplicación, TTS sincronizado, ejecución programada, packaging, seguridad, tests y auditorías.

## Cambios posteriores a la última release publicada

La rama `main` contiene actualmente cambios posteriores a la release `1.2.2`. No deben describirse como parte de esa release hasta que exista una nueva release que los incluya.

### PR #20 — Safe video concurrency

**Estado:** fusionada en `main` después de `1.2.2`.

**Tipo de cambio:** funcional/performance/estabilidad.

La implementación modifica `safe_parallelism()` para que:

- `max_parallel_videos = 0` signifique **AUTO** en lugar de convertirse implícitamente en un único worker;
- se resuelva primero el dispositivo/modelo efectivo de Whisper;
- se calcule un techo conservador según CPU y RAM disponibles;
- se tenga en cuenta la memoria GPU disponible cuando se utiliza CUDA;
- los valores positivos configurados actúen como límite superior y puedan ser recortados si superan la capacidad segura;
- `max_parallel_videos = 1` continúe garantizando un único worker.

La PR incorpora tests específicos para AUTO, clamping por hardware y single-worker. Esta funcionalidad pertenece al estado actual de `main`, pero **no pertenece a la release publicada `1.2.2`**.

### PR #21 — Package metadata alignment

**Estado:** fusionada en `main` después de `1.2.2`.

**Tipo de cambio:** corrección de metadata.

Actualiza `project.version` en `pyproject.toml` de `1.0.0` a `1.2.2` para que el metadata del paquete coincida con la release ya publicada. No introduce una funcionalidad de producto nueva ni debe contarse como una funcionalidad de `1.2.2`.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.

## Estado actual del versionado

La última release publicada sigue siendo `1.2.2`. El `pyproject.toml` actual declara también `1.2.2` debido a PR #21. Sin embargo, `main` contiene además cambios funcionales posteriores a esa release, principalmente la concurrencia adaptativa de PR #20.

Por tanto, **la versión publicada y la versión del paquete no deben interpretarse como una descripción completa de todas las capacidades presentes en `main`**. Hasta que se publique una nueva release, las funcionalidades posteriores deben identificarse explícitamente como cambios post-`1.2.2`.
