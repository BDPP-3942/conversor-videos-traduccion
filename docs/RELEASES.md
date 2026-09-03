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
| Endurecimiento de extracción ZIP y componentes de filesystem multiplataforma | `1.5.1` |
| Traducción local opcional, runtime GPU/CPU endurecido y gestión reproducible de recursos | `1.5.2` |

## Releases publicadas

### 1.5.1 — ZIP Extraction & Cross-Platform Filesystem Hardening

**Tipo:** `PATCH`.

**Commit/tag publicado:** `06ee8d265b57214596f079f3bb426b9b27042b1e` / `v1.5.1`.

- Protección contra rutas absolutas POSIX y Windows, UNC y traversal con separadores multiplataforma.
- Protección contra symlinks y nombres reservados de Windows.
- Detección preventiva de colisiones por case y normalización Unicode.
- Prevención de sobrescritura silenciosa de entradas ZIP duplicadas.
- Sanitización de componentes de filesystem generados por la aplicación.
- Validación multiplataforma y endurecimiento de la integridad de extracción.
- Release publicada el 3 de septiembre de 2026.

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR`.

**Commit/tag publicado:** `261f4b475f452b98880815f722aa8f8f43d28097` / `v1.5.0`.

- Dispatcher común para `run_local.sh` y `run_local.bat`.
- Política de naming validada contra el árbol de referencia.
- Soporte de `whisper_initial_prompt` mediante texto literal y archivos de contexto.
- Estrategia documentada de ejecución CPU/GPU con CTranslate2.
- Validación multiplataforma de tests, packaging y entry points.
- Release publicada el 1 de septiembre de 2026.

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

## Candidata 1.5.2

### Alcance

**Tipo:** `PATCH`.

La candidata 1.5.2 añade un proveedor opcional de traducción local, endurece la detección y selección del runtime GPU/CPU y hace reproducible la preparación de los recursos locales. No requiere NVIDIA/CUDA/Internet/Ollama/LM Studio para la ejecución CPU normal una vez preparados los recursos necesarios.

### Cambios

- Proveedor local español→inglés basado en CTranslate2 + SentencePiece.
- Modelo y revisión fijados con validación de tamaño y SHA-256.
- Descarga HTTPS controlada, temporales, reanudación cuando es posible y reemplazo atómico.
- Fallback configurable ante ausencia/corrupción del recurso local.
- Detección NVIDIA condicionada a capacidad CUDA real de CTranslate2; AMD/Intel/Apple no se declaran compatibles sin un backend verificado.
- Selección automática CPU `int8` cuando CUDA no está disponible o falla su inicialización.
- Scripts explícitos para preparar, inspeccionar y limpiar el recurso local.
- Runtime NVIDIA gestionado bajo `tools/cuda/` con instalación interactiva de las bibliotecas necesarias cuando el diagnóstico detecta una GPU NVIDIA sin runtime compatible.

### Estado

La candidata no debe considerarse publicada hasta completar CI, tests, seguridad, packaging, documentación y validación de un único SHA final. El tag `v1.5.2` no se crea durante la preparación de la candidata.

## Candidata 1.4.1

La documentación histórica de esta candidata se conserva para trazabilidad. La release posterior `1.4.2` y el resto del historial publicado mantienen sus respectivos registros.

## Política de tags

Los tags de release utilizan el formato `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.3.0` permanece asociado a `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`, `v1.4.0` permanece asociado a `ce1da6ea69a89f5a789c0670b200d6038f1a746d`, `v1.5.0` permanece asociado a `261f4b475f452b98880815f722aa8f8f43d28097` y `v1.5.1` permanece asociado a `06ee8d265b57214596f079f3bb426b9b27042b1e`. Ninguno debe modificarse.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
