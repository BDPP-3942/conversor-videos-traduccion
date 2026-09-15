# Histórico de releases

Este documento registra el alcance funcional de cada versión. Las releases de GitHub y sus tags son la referencia del código publicado; este documento conserva el contexto humano de los cambios.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR:** cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.

Una release agrupa un conjunto funcional coherente. Los tags publicados son inmutables.

## Releases publicadas

### 1.8.2 — Corrección de descarga y revisión de MADLAD

**Tipo:** `PATCH` · **Tag:** `v1.8.2` · **Estado:** publicada.

- Corrige la revisión fijada de MADLAD-400 3B CT2 INT8.
- Corrige el tokenizer real a `spiece.model`.
- Mantiene validación de tamaño y SHA-256.
- Diferencia diagnósticos `404` de errores `401/403` de Hugging Face.
- Corrige fixtures de integridad y alinea metadatos de aplicación, empaquetado y documentación.

### 1.8.1 — Bootstrap gestionado de uv y traducción local opcional

**Tipo:** `PATCH` · **Tag:** `v1.8.1` · **Estado:** publicada.

- Añade bootstrap gestionado de uv sin instalación global obligatoria.
- Permite preparar opcionalmente el modelo local de traducción durante el setup.
- Mantiene la descarga diferida mediante `manage_local_translation.py`.

### 1.8.0 — Recuperación Whisper y traducción local

**Tipo:** `MINOR` · **Tag:** `v1.8.0` · **Estado:** publicada.

- Refina la recuperación selectiva de Whisper y separa VAD de la división de subtítulos.
- Incorpora MADLAD-400 3B CT2 INT8 como modelo local predeterminado y conserva OPUS-MT como alternativa ligera.
- Refuerza integridad, tokenización, revisiones fijadas y selección de modelos.

### 1.7.4 — Validación de uv y traducción local

**Tipo:** `PATCH` · **Estado:** publicada.

- Valida `shared_vocabulary.json` según la estructura real del artefacto fijado.
- Consolida la migración reproducible de desarrollo, CI, build y auditoría a uv.

### 1.7.3 — Metadatos del modelo local

**Tipo:** `PATCH` · **Estado:** publicada.

- Empaqueta los metadatos JSON necesarios para la revisión fijada del modelo local.

### 1.7.2 — Corrección de descarga del modelo local

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el límite y el recorrido de los artefactos del modelo local.

### 1.7.1 — Compatibilidad de recuperación STT

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el contrato de `clip_timestamps` de `faster-whisper`.

### 1.7.0 — Regeneración, nombres Unicode y runtime de traducción

**Tipo:** `MINOR` · **Estado:** publicada.

- Consolida regeneración y manifests.
- Refuerza naming determinista, Unicode, límites de filesystem y colisiones.
- Consolida traducción local CTranslate2 + SentencePiece y su validación.

### 1.6.0 — Traducción local y endurecimiento del runtime GPU

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce traducción local opcional, recuperación STT configurable y runtime GPU gestionado.

### 1.5.1 — Extracción ZIP y endurecimiento multiplataforma

**Tipo:** `PATCH` · **Estado:** publicada.

- Endurece traversal ZIP, rutas absolutas/UNC, symlinks, nombres reservados y colisiones Unicode/case.

### 1.5.0 — Whisper multiplataforma, contexto y empaquetado

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce wrappers multiplataforma, contexto externo de Whisper y empaquetado reproducible.

### 1.4.2 — Contrato CLI de regeneración

**Tipo:** `PATCH` · **Estado:** publicada.

- Amplía y documenta el contrato CLI de regeneración.

### 1.4.1 — Integración de regeneración en scripts

**Tipo:** `PATCH` · **Estado:** publicada.

- Integra la regeneración en wrappers sin duplicar la lógica del pipeline.

### 1.4.0 — Regeneración limpia y endurecimiento de release

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce regeneración limpia, backup/restauración y endurecimiento de release.

### 1.3.0 — Concurrencia adaptada a recursos

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce concurrencia adaptativa basada en CPU/RAM/GPU.

### 1.2.2 — Limpieza de timestamps del naming

**Tipo:** `PATCH` · **Estado:** publicada.

- Elimina timestamps técnicos de nombres y resultados.

### 1.2.1 — Corrección de instalación TTS

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige la instalación multiplataforma de recursos TTS.

### 1.2.0 — Mejoras de naming y TTS

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación VTT e integración TTS

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce recuperación VTT, regeneración selectiva y TTS sincronizado.

### 1.0.1 — Documentación de instalación y mantenimiento

**Tipo:** `PATCH` · **Estado:** publicada.

- Añade y corrige documentación inicial de instalación.

### 1.0.0 — Primera release estable

Primera release estable de esta línea de producto.

## Release candidate actual: 1.9.0

**Tipo:** `MINOR` · **Tag objetivo:** `v1.9.0` · **Estado:** no publicada.

### Resumen funcional

`1.9.0` incorpora una aplicación GUI de escritorio y la infraestructura de distribución nativa, sin sustituir el pipeline existente ni eliminar la CLI o la ejecución programada.

### Cambios de producto

- Nuevo entry point `video-translation-desktop`.
- Fachada `VideoTranslationApplication` para separar interfaz y lógica de aplicación.
- Adaptador `ControllableMediaPipeline` sobre `MediaPipeline`, con eventos de etapa, progreso y cancelación cooperativa.
- GUI para procesamiento, recuperación de subtítulos, duplicados, diagnóstico y consulta de CLI/programación.
- Configuración GUI de almacenamiento local/Google Drive/rclone, idiomas, proveedores y fallbacks, concurrencia, Whisper, WebM, TTS, resume y naming.
- Selección de archivo de contexto para el prompt inicial de Whisper.
- Recuperación `full`, `stt_only` y `translate_only`.
- Deduplicación mediante análisis, simulación y eliminación confirmada.
- ZIP: reparación específica de nombres UTF-8 mal decodificados como CP437 cuando falta el indicador UTF-8, sin alterar nombres CP437 legítimos.

### Almacenamiento de escritorio

- `input` y `output` dejan de depender de una carpeta privada de datos de aplicación.
- Los valores predeterminados de trabajo se sitúan en `Documentos/Video Translation Pipeline/input` y `output`.
- El estado técnico, logs, cachés y otros datos internos permanecen en el directorio privado de datos del usuario.
- La GUI permite seleccionar carpetas externas compartidas, de red o sincronizadas cuando el usuario dispone de permisos de escritura.
- La aplicación no necesita escribir en `Program Files` para procesar vídeos.

### Cambios de distribución

- Windows: ejecutable PyInstaller y MSI mediante WiX 6.
- En Windows x64, el instalador x64 utiliza el `Program Files` nativo y no `Program Files (x86)`.
- El proyecto no declara que un ejecutable x64 pueda funcionar en Windows x86. Si se publica una variante x86, debe construirse y validarse realmente con un entorno Python x86 y dependencias compatibles.
- El instalador crea un acceso directo en el menú Inicio.
- macOS: `.app` + ZIP de distribución.
- Linux: ejecutable PyInstaller + AppDir + AppRun + `.desktop` + SVG + AppImage x86_64.

### Cambios de CI/CD y release

- Workflow de empaquetado nativo en Linux, Windows y macOS.
- Validación de ejecutables e instaladores por plataforma.
- Workflow de release activado por `vX.Y.Z`.
- Build automático en runners nativos.
- Adjuntar automático de `.AppImage`, MSI y ZIP de macOS a la GitHub Release.
- Los ZIP/TAR del código fuente continúan siendo generados automáticamente por GitHub para el tag.
- El proceso normal de publicación no requiere build local ni subida manual de binarios.

### Documentación y CLI

- La referencia de CLI se amplía con casos de uso para procesamiento normal, `dry-run`, programación, regeneración, recuperación de subtítulos, duplicados, proveedores, diagnóstico, wrappers y traducción local.
- Los documentos modificados incluyen enlaces Markdown relativos a los documentos relacionados en lugar de mencionar archivos sin navegación.
- La documentación de escritorio registra explícitamente la separación entre instalación, datos multimedia y estado privado.
- La release candidate se documenta como `1.9.0`; la publicación de `v1.9.0` queda condicionada a CI, Release Gate y merge a `main`.

### Compatibilidad

- Se conservan `video-translation-pipeline`, regeneración, QA de subtítulos y TTS.
- Se conserva la ejecución programada/headless.
- No se introduce soporte móvil.
- No se embeben credenciales ni modelos privados en los binarios.

### Validación obligatoria antes de publicar `v1.9.0`

Deben pasar sobre el SHA final de la rama:

```bash
uv lock --check
uv run ruff check . --select F401,I001
uv run ruff check .
uv run ruff check . --select S
uv run ruff format --check .
uv run python -m compileall .
uv run pytest -q --ignore=tests/test_packaging.py
uv build
```

Además, CI debe construir y validar los artefactos nativos de escritorio. No se debe publicar `v1.9.0` mientras exista un fallo de calidad, empaquetado o Release Gate.

## Funcionalidades con evidencia de introducción

| Funcionalidad | Primera versión verificada |
| --- | ---: |
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación VTT e integración TTS | `1.1.0` |
| Naming descriptivo y bootstrap de Kokoro | `1.2.0` |
| Concurrencia adaptada a CPU/RAM/GPU | `1.3.0` |
| Regeneración limpia desde fuente | `1.4.0` |
| Endurecimiento ZIP/filesystem | `1.5.1` |
| Traducción local y runtime GPU | `1.6.0` |
| Reprocessing, manifests y naming Unicode | `1.7.0` |
| MADLAD-400 3B y recuperación Whisper refinada | `1.8.0` |
| Bootstrap gestionado de uv | `1.8.1` |
| Corrección de MADLAD y tokenizer | `1.8.2` |
| Resolución compartida de uv | `1.8.3` candidata histórica |
| Aplicación GUI, empaquetado nativo, reparación ZIP Unicode y arquitectura de almacenamiento de escritorio | `1.9.0` candidata |

## Integridad histórica

Las versiones publicadas no se reescriben. La documentación de `1.9.0` describe exclusivamente el nuevo alcance de escritorio, la reparación Unicode, el almacenamiento de trabajo y la automatización de release. El soporte móvil permanece fuera del producto.
