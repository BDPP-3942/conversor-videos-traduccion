# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La versión del proyecto no debe incrementarse por cada commit de formato o CI. Una release agrupa un conjunto funcional coherente.

## Funcionalidades con evidencia de introducción

| Funcionalidad | Primera versión verificada |
|---|---:|
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS sincronizado, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación de VTT e integración TTS en el pipeline común | `1.1.0` |
| Naming descriptivo/más resistente a colisiones y bootstrap de assets TTS | `1.2.0` |
| Corrección de instalación de assets TTS en Windows y consistencia multiplataforma | `1.2.1` |
| Limpieza de timestamps técnicos en naming | `1.2.2` |
| Concurrencia de vídeo adaptada a recursos (CPU/RAM/GPU) | `1.3.0` |

## Releases publicadas

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

## Cambios incorporados en 1.3.0

### PR #20 — Safe video concurrency

**Tipo de cambio:** funcional/performance/estabilidad.

- `max_parallel_videos = 0` significa **AUTO**.
- Se resuelve primero el dispositivo/modelo efectivo de Whisper.
- Se calcula un techo conservador según CPU y RAM disponibles.
- Se tiene en cuenta la memoria GPU disponible cuando se utiliza CUDA.
- Los valores positivos actúan como límite superior y se recortan si superan la capacidad segura.
- `max_parallel_videos = 1` continúa garantizando un único worker.
- Se incorporan regresiones para AUTO, clamping por hardware y single-worker.

### PR #21 — Package metadata alignment

**Tipo de cambio:** packaging/metadata.

- Alinea inicialmente `project.version` con la última release publicada antes de preparar `1.3.0`.
- No introduce funcionalidad de producto independiente.

### PR #22 — Documentation update

**Tipo de cambio:** documentación.

- Registra los cambios posteriores a `1.2.2` incorporados en `main`.
- Actualiza la documentación para mantener trazabilidad de los cambios antes de la nueva release.

## Política de tags

Los tags de release utilizan el formato `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.2.2` permanece asociado al estado publicado de `1.2.2`. La nueva release se publicará con un tag independiente, `v1.3.0`.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
