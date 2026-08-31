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
| Regeneración limpia explícita de resultados existentes | `1.4.0` |

## Releases publicadas

### 1.3.0 — Safe Resource-Aware Video Concurrency

**Tipo:** `MINOR`.

**Commit/tag publicado:** `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` / `v1.3.0`.

- `max_parallel_videos = 0` significa AUTO.
- El límite efectivo se calcula de forma conservadora según CPU/RAM/GPU.
- Los valores positivos actúan como límites superiores sujetos al techo seguro.
- Se incorporan las PR #20, #21 y #22 como conjunto funcional preparado por la PR #23.

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH`.

Publicado el 28 de agosto de 2026.

- Evita incorporar metadatos de fecha/hora de ZIP, carpetas extraídas o nombres de origen en la descripción del curso.
- Amplía la limpieza de formatos de fecha y datetime antes de extraer números/descripciones de curso y lección.
- Mantiene la convención `[course_number]_[course_description]x[lesson_number]_[lesson_description]` cuando la información está disponible.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH`.

Publicado el 28 de agosto de 2026.

- Corrige la instalación de modelos TTS en Windows cuando un archivo temporal estaba todavía abierto (`WinError 32`).
- Hace consistente la instalación de recursos TTS entre Windows, Linux y macOS.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR`.

Publicado el 28 de agosto de 2026.

- Introduce la convención de nombres descriptiva para curso/lección.
- Mejora la detección de información de curso y lección y el bootstrap de assets Kokoro.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR`.

- Recuperación de VTT originales/traducidos inválidos o ausentes.
- Regeneración selectiva de STT o traducción sin regenerar el vídeo normal.
- Validación final de timestamps después de segmentación STT.
- Integración de TTS en el pipeline común.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH`.

- Añade la guía de instalación y corrige la navegación documental.

### 1.0.0 — Primera release estable

**Tipo:** primera release de producto de esta línea.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.

## Cambios incluidos en 1.4.0 — candidata

### PR #24 — Explicit clean video regeneration

**Tipo:** `FEATURE`.

- Añade `src.regeneration` y `video-translation-regenerate`.
- Localiza resultados registrados mediante manifest.
- Aparta los resultados anteriores mediante backup antes de regenerar.
- Reutiliza `MediaPipeline` para el procesamiento desde la fuente.
- Limpia backups solo después del éxito.
- Intenta restaurar backups ante fallo.
- Mantiene la fuente original intacta.

### PR #25 — Repository governance and hygiene

**Tipo:** `GOVERNANCE / DOCUMENTATION`.

- Añade reglas de branches, Conventional Commits, PRs y release hygiene.
- Retira el workflow one-off de formato.
- Mantiene CI como comprobación de formato sin escritura en ramas.

### Hardening de release — PR #26

**Tipo:** `FIX / SECURITY / QA / ARCHITECTURE`.

- El cálculo efectivo de concurrencia permanece sujeto al límite seguro de recursos incluso con overrides CLI.
- La regeneración usa el contrato explícito de `StorageProvider` para la limpieza de resultados.
- Local, Google Drive y rclone mantienen sus operaciones destructivas dentro de sus adaptadores.
- Se validan los caminos de éxito y rollback de regeneración.
- Se incorporan comprobaciones E2E/CLI de los contratos de release.

## Estado de la candidata

La rama `release/1.4.0-hardening` parte exactamente de `main` en `250fd2d239848c4f1f9b82485f602728b46cf71f`. La candidata aún no está publicada y no existe `v1.4.0`.

La publicación requiere un SHA candidato final con CI verde sobre ese mismo SHA, validación de packaging, seguridad, tests y documentación, y solo entonces un tag inmutable `v1.4.0` sobre ese commit.

## Política de tags

Los tags de release utilizan el formato `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.3.0` permanece asociado a `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` y no debe modificarse.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
