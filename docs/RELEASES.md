# Histórico de releases

Este documento registra el alcance funcional de cada versión. Las releases de GitHub y sus tags son la referencia del código publicado; este documento conserva el contexto humano de los cambios.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR:** cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.

Una release agrupa un conjunto funcional coherente. Los tags publicados son inmutables.

## Releases publicadas

### 1.8.2 — MADLAD model download and Hugging Face revision fix

**Tipo:** `PATCH` · **Tag:** `v1.8.2` · **Estado:** publicada.

- Corrige la revisión fijada de MADLAD-400 3B CT2 INT8.
- Corrige el tokenizer real a `spiece.model`.
- Mantiene validación de tamaño y SHA-256.
- Diferencia diagnósticos `404` de errores `401/403` de Hugging Face.
- Corrige fixtures de integridad y alinea metadatos de aplicación, packaging y documentación.

### 1.8.1 — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** `PATCH` · **Tag:** `v1.8.1` · **Estado:** publicada.

- Añade bootstrap gestionado de uv sin instalación global obligatoria.
- Permite preparar opcionalmente el modelo local de traducción durante setup.
- Mantiene la descarga diferida mediante `manage_local_translation.py`.
- Actualiza instalación, migración, README, regresiones y lockfile.

### 1.8.0 — Whisper Recovery & Local Translation

**Tipo:** `MINOR` · **Tag:** `v1.8.0` · **Estado:** publicada.

- Refina la recuperación selectiva de Whisper y separa VAD de split de subtítulos.
- Incorpora MADLAD-400 3B CT2 INT8 como modelo local predeterminado y conserva OPUS-MT como alternativa ligera.
- Refuerza integridad, tokenización, revisiones fijadas y selección de modelos.
- Actualiza el contexto de Whisper y mantiene la infraestructura reproducible con uv.

### 1.7.4 — uv and Local Translation Validation

**Tipo:** `PATCH` · **Estado:** publicada.

- Valida `shared_vocabulary.json` con raíz array cuando corresponde al artefacto real.
- Mantiene validación estricta de los JSON de configuración.
- Consolida la migración reproducible de desarrollo, CI, build y auditoría a uv.

### 1.7.3 — Local Translation Model Metadata Bootstrap

**Tipo:** `PATCH` · **Estado:** publicada.

- Empaqueta `config.json` y `tokenizer_config.json` de la revisión fijada.
- Reduce descargas externas de metadatos pequeños y mantiene validación del resto de artefactos.

### 1.7.2 — Local Translation Model Download Fix

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el cálculo del límite y el recorrido de artefactos del modelo local.
- Añade regresiones de descarga, preparación e inicialización del proveedor.

### 1.7.1 — STT Selective Recovery Compatibility

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el contrato numérico de `clip_timestamps` de `faster-whisper`.
- Añade regresiones de recuperación STT.

### 1.7.0 — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** `MINOR` · **Estado:** publicada.

- Consolida reprocessing y manifests.
- Refuerza naming determinista, Unicode NFC/NFD, límites de filesystem y colisiones.
- Consolida traducción local CTranslate2 + SentencePiece y su validación.

### 1.6.0 — Local Translation & GPU Runtime Hardening

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce traducción local opcional, recuperación STT configurable y runtime GPU gestionado.

### 1.5.1 — ZIP Extraction & Cross-Platform Filesystem Hardening

**Tipo:** `PATCH` · **Estado:** publicada.

- Endurece ZIP traversal, rutas absolutas/UNC, symlinks, nombres reservados y colisiones Unicode/case.

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce wrappers multiplataforma, contexto externo de Whisper y packaging reproducible.

### 1.4.2 — Regeneration CLI Contract and Help Alignment

**Tipo:** `PATCH` · **Estado:** publicada.

- Amplía y documenta el contrato CLI de regeneración.

### 1.4.1 — Corrective Script Integration

**Tipo:** `PATCH` · **Estado:** publicada.

- Integra la regeneración en wrappers sin duplicar lógica del pipeline.

### 1.4.0 — Clean Video Regeneration and Release Hardening

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce regeneración limpia, backup/restauración y endurecimiento de release.

### 1.3.0 — Safe Resource-Aware Video Concurrency

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce concurrencia adaptativa basada en CPU/RAM/GPU.

### 1.2.2 — Naming Timestamp Cleanup

**Tipo:** `PATCH` · **Estado:** publicada.

- Elimina timestamps técnicos de nombres y resultados.

### 1.2.1 — TTS Installation Fix

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige la instalación multiplataforma de recursos TTS.

### 1.2.0 — Naming and TTS Improvements

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación de VTT e integración TTS

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce recuperación de VTT, regeneración selectiva y TTS sincronizado.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH` · **Estado:** publicada.

- Añade y corrige documentación inicial de instalación.

### 1.0.0 — Primera release estable

Primera release estable de esta línea de producto.

## Release candidate actual: 1.9.0

**Tipo:** `MINOR` · **Tag objetivo:** `v1.9.0` · **Estado:** no publicada.

### Resumen funcional

`1.9.0` añade la aplicación GUI de escritorio y la infraestructura de distribución nativa sin sustituir el pipeline existente ni eliminar CLI/scheduling.

### Cambios de producto

- Nuevo entry point `video-translation-desktop`.
- Fachada `VideoTranslationApplication` para separar UI y lógica de aplicación.
- Adaptador `ControllableMediaPipeline` sobre `MediaPipeline`, con eventos de etapa y cancelación cooperativa.
- GUI con pestañas de Process, Subtitle Recovery, Duplicates, Diagnostics y CLI/Scheduling.
- Configuración GUI de almacenamiento local/Google Drive/rclone, idiomas, proveedores y fallbacks, concurrencia, Whisper, WebM, TTS, resume y naming.
- Recuperación `full`, `stt_only` y `translate_only`.
- Deduplicación mediante scan, análisis, dry-run y eliminación confirmada.
- Diagnósticos y preparación de Whisper.
- UX de ejecución en background, progreso, logs, estado, errores y cancelación en límites seguros.

### Cambios de distribución

- Windows: PyInstaller `.exe` + MSI WiX 6.0.2.
- macOS: `.app` + ZIP de distribución.
- Linux: ejecutable PyInstaller + AppDir + AppRun + `.desktop` + SVG + AppImage x86_64.

Linux no necesita un método distinto para construir la GUI: PyInstaller genera el mismo tipo de ejecutable de escritorio; AppImage es la capa de distribución portable que lo contiene junto con su metadata de integración con el escritorio.

### Cambios de CI/CD y release

- Workflow de packaging nativo en Linux, Windows y macOS.
- Validación de ejecutables/instaladores por plataforma.
- Workflow de release activado por `vX.Y.Z`.
- Build automático en runners nativos.
- Adjuntar automático de `.AppImage`, `.msi` y ZIP del `.app` a la GitHub Release.
- Los ZIP/TAR de código fuente continúan siendo generados automáticamente por GitHub para el tag.
- El proceso normal de publicación ya no requiere build local ni subida manual de binarios.

### Compatibilidad

- Se conservan `video-translation-pipeline`, regeneración, subtitle-QA y TTS.
- Se conserva ejecución programada/headless.
- No se introduce soporte móvil.
- No se embeben credenciales ni modelos privados en los binarios.

### Versionado y validación

`1.9.0` es MINOR porque todo lo anterior es funcionalidad nueva compatible hacia atrás. Antes de crear `v1.9.0` deben estar sincronizados `pyproject.toml`, `config/app.toml`, `uv.lock`, `CHANGELOG.md` y la documentación de release, y debe pasar CI + Release Gate sobre el SHA final de `main`.

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
| Compatibilidad `clip_timestamps` en recuperación STT | `1.7.1` |
| Corrección de descarga del modelo local | `1.7.2` |
| Bootstrap de metadatos JSON del modelo local | `1.7.3` |
| Validación de `shared_vocabulary.json` y migración reproducible a uv | `1.7.4` |
| Recuperación STT refinada y modelos locales fijados, MADLAD-400 3B y OPUS-MT | `1.8.0` |
| Bootstrap gestionado de uv y preparación opcional de traducción local | `1.8.1` |
| Corrección de recurso MADLAD, tokenizer, fixtures y diagnóstico de descarga | `1.8.2` |
| Resolución compartida de uv en wrappers POSIX/Windows | `1.8.3` candidata histórica |
| Aplicación GUI, control de pipeline, empaquetado nativo y publicación automática de artefactos | `1.9.0` candidata |

## Integridad histórica

Las versiones publicadas no se reescriben. `1.8.0`, `1.8.1` y `1.8.2` permanecen como historia publicada. La documentación de `1.9.0` describe exclusivamente el nuevo alcance de escritorio y release automation. El alcance móvil permanece fuera del producto.
