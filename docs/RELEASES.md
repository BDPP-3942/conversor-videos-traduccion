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
| Integración de la regeneración existente en los wrappers locales | `1.4.1` |
| Wrappers multiplataforma con forwarding exacto, naming de referencia y contexto externo de Whisper | `1.5.0` |

## Candidata 1.5.0

**Tipo propuesto:** `MINOR`.

**Estado:** candidata en PR #33; no publicada hasta completar el Release Gate.

Alcance funcional:

- dispatcher común para `run_local.sh` y `run_local.bat`;
- forwarding exacto de argumentos y soporte explícito de `run`/`regenerate`;
- política de naming validada contra el árbol completo de `arbol_zips.txt`;
- `whisper_initial_prompt` mediante prompt literal o `txt`, `md`, `csv` y `docx`;
- documentación de la estrategia real de CPU/GPU de CTranslate2 sin afirmar partición de una inferencia entre ambos dispositivos;
- CI de tests sobre Linux, Windows y macOS para Python 3.11, 3.12 y 3.13;
- packaging del recurso `palabras_contexto.*`.

La versión `1.5.0` solo se considera publicada cuando un único SHA final tenga CI, tests, seguridad, packaging y documentación completos y el tag correspondiente apunte exactamente a ese SHA.

## Releases publicadas

### 1.4.0 — Clean Video Regeneration & Release Hardening

**Tipo:** `MINOR`.

**Commit/tag publicado:** `ce1da6ea69a89f5a789c0670b200d6038f1a746d` / `v1.4.0`.

- Regeneración limpia mediante el `MediaPipeline` común.
- Contrato público de `StorageProvider` para backup, restore y eliminación.
- Concurrencia segura también para overrides CLI.
- CI, packaging, seguridad y E2E de release validados.

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

## Candidata 1.4.1

### Alcance

**Tipo:** `PATCH`.

La candidata 1.4.1 no añade un pipeline nuevo. Integra en `scripts/run_local.sh` y `scripts/run_local.bat` la operación de regeneración ya existente mediante `src.regeneration` / `video-translation-regenerate`.

### PR de release

- Rama: `release/1.4.1-correction`.
- Base: `main`, sobre la release publicada `v1.4.0`.
- Nueva PR específica de la release; no reutiliza PR #26.

### Estado

La candidata no debe considerarse publicada hasta completar el Release Gate, CI, E2E, packaging, seguridad y validación de un único SHA final. El tag `v1.4.1` no se crea durante la preparación de la candidata.

## Política de tags

Los tags de release utilizan el formato `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.3.0` permanece asociado a `620af6acbe3fca7d42ccd57f3585b3952cccf0a7` y no debe modificarse. `v1.4.0` permanece asociado al commit de `main` `ce1da6ea69a89f5a789c0670b200d6038f1a746d` y tampoco debe modificarse.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
