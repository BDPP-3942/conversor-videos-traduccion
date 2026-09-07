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
| Traducción local opcional, recuperación STT configurable y endurecimiento GPU/runtime | `1.6.0` |
| Reprocessing/manifests, consolidación de naming Unicode/filesystem y mejoras del runtime de traducción local | `1.7.0` |
| Corrección del contrato `clip_timestamps` en la recuperación selectiva de STT con `faster-whisper` | `1.7.1` |
| Corrección de descarga del modelo local y validación del flujo proveedor-modelo | `1.7.2` |

## Releases publicadas

### 1.7.0 — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** `MINOR`.

**Tag publicado:** `v1.7.0`.

Esta es la **release publicada más reciente confirmada** antes de la línea candidata 1.7.2. Consolida el reprocesado y la persistencia de manifests, refuerza el almacenamiento local multiplataforma, consolida el naming determinista y la normalización Unicode, endurece los límites reales de filesystem y consolida el proveedor de traducción local y su runtime.

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

## Candidata 1.7.2

### Posición en la línea de releases

**Tipo:** `PATCH`.

`1.7.2` es una release de mantenimiento del estado `1.7.1`, que contiene la corrección previa de recuperación selectiva STT. La release publicada más reciente confirmada sigue siendo `v1.7.0` hasta que se publique formalmente `v1.7.1`.

Por tanto:

- **Previous functional state:** `1.7.1` integrado en `main`.
- **Published release:** `v1.7.0`.
- **Baseline funcional inmediato:** estado completo de `1.7.1`.
- **Target tag:** `v1.7.2` — pendiente de validación y creación.

### Alcance

La candidata `1.7.2` corrige el gestor de descarga del modelo de traducción local. El código anterior calculaba el límite con una expresión equivalente a `MODEL_FILES.get(name, (0, SMALL_MODEL_FILES[name][0]))[1]`. El argumento por defecto de `dict.get` se evalúa antes de la llamada, por lo que `SMALL_MODEL_FILES['model.bin']` provocaba `KeyError` aunque `model.bin` sí existiera en `MODEL_FILES`.

La corrección selecciona explícitamente el límite correspondiente al fichero actual. Esto permite que la preparación alcance la descarga de los tres ficheros principales y los tres metadatos, manteniendo las validaciones de integridad y el reemplazo atómico.

### Cambios

- Corregido el cálculo del límite de descarga para separar ficheros principales y metadatos.
- Añadida regresión que recorre todos los ficheros gestionados durante `LocalTranslationModelManager.download()`.
- Añadida regresión que prepara el modelo y verifica la inicialización del proveedor y una llamada de traducción mediante las fronteras CTranslate2/SentencePiece.
- Documentada la causa del `KeyError: 'model.bin'` y el procedimiento de validación real con el benchmark.
- Conservada la descarga pública sin autenticación y el token opcional para entornos que lo requieran.
- Conservada la revisión/modelo fijados y la validación por tamaño, SHA-256 y estructura de metadatos.
- Conservada la corrección `clip_timestamps` de `1.7.1`.

### Dependencias

La candidata mantiene el stack compatible actualmente declarado por el proyecto:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`

### Validación

La candidata final pre-merge debe completar CI y Release Gate sobre su SHA exacto, incluyendo Linux, Windows y macOS con Python 3.11–3.13, tests, lint/security/format, compile, audits, packaging, instalación limpia, `pip check` y entry points.

Además, en el entorno macOS objetivo debe ejecutarse:

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
python scripts/manage_local_translation.py status
python scripts/benchmark_local_translation.py --sentences 1
```

El benchmark constituye la prueba funcional real de carga y traducción del modelo preparado; los tests CI utilizan dobles deterministas para evitar descargar 78.7 MiB en cada runner.

### Política de tags

Los tags utilizan `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.7.0`, `v1.6.0`, `v1.5.1` y las releases anteriores permanecen asociados a sus commits publicados y no deben modificarse. `v1.7.1` y `v1.7.2` solo deben crearse sobre los SHA exactos validados por Release Gate.

## Historial anterior

Antes de la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
