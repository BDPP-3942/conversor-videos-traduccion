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
| Wrappers multiplataforma, naming de referencia y contexto externo de Whisper | `1.5.0` |
| Endurecimiento ZIP/filesystem multiplataforma | `1.5.1` |
| Traducción local opcional y endurecimiento GPU/runtime | `1.5.2` |

## Releases publicadas

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

## Candidata 1.5.2

### Alcance

**Tipo:** `PATCH`.

La candidata 1.5.2 añade traducción local opcional español→inglés mediante CTranslate2 + SentencePiece, endurece la selección GPU/CPU y hace reproducible la preparación de recursos locales. No requiere NVIDIA/CUDA/Internet/Ollama/LM Studio para una ejecución CPU local una vez preparados los recursos necesarios.

### Cambios

- Modelo y revisión fijados.
- `model.bin`, `source.spm` y `target.spm` validados por tamaño y SHA-256.
- Metadatos JSON requeridos validados por presencia, tamaño, UTF-8, tipo y estructura mínima.
- Descarga HTTPS controlada, temporales, reanudación cuando es posible y reemplazo atómico.
- Fallback configurable cuando el recurso local no está disponible.
- Detección NVIDIA condicionada a capacidad real de CTranslate2.
- Fallback CPU `int8` cuando CUDA no puede validarse.
- Runtime NVIDIA gestionado bajo `tools/cuda/` con cuBLAS CUDA 12 y cuDNN 9.
- Recuperación selectiva de segmentos STT sospechosos.
- Endurecimiento ZIP/filesystem heredado de 1.5.1.

### Configuración

La configuración general sigue en `config/app.toml` con overrides de entorno. La configuración específica de traducción local usa exclusivamente `LOCAL_TRANSLATION_*`; no existe una sección `[local_translation]` duplicada en TOML.

### Estado

La candidata no se considera publicada hasta que el SHA final tenga CI y Release Gate satisfactorios. El tag `v1.5.2` se creará únicamente después del merge y sobre el SHA exacto resultante de `main`. No se declara ningún benchmark GPU ni prueba A/B de un MP4 externo que no esté disponible en el repositorio.

## Política de tags

Los tags utilizan `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.3.0`, `v1.4.0`, `v1.5.0` y `v1.5.1` permanecen asociados a sus commits publicados anteriores y no deben modificarse.

## Historial anterior

Antes de la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
