# Histórico de releases

Este documento registra el alcance funcional de cada versión. Las releases de GitHub y sus tags son la referencia del código publicado; este documento conserva el contexto humano de los cambios.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR:** cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.

Los tags publicados son inmutables.

## Releases publicadas

### 1.9.0 — Aplicación de escritorio y distribución nativa

**Tipo:** `MINOR` · **Tag:** `v1.9.0` · **Estado:** publicada.

- Introduce la GUI de escritorio como capa sobre el pipeline existente.
- Añade empaquetado nativo para Windows, macOS y Linux y publicación automática de artefactos.
- Mantiene CLI, ejecución programada/headless, regeneración, QA y TTS.

### 1.8.3 — Resolución gestionada de uv

**Tipo:** `PATCH` · **Estado:** publicada.

- Añade resolución compartida de `uv` en wrappers POSIX y Windows.
- Conserva el fallback a `PATH` y al entorno `.venv` cuando corresponde.

### 1.8.2 — Corrección de MADLAD y diagnóstico de Hugging Face

**Tipo:** `PATCH` · **Tag:** `v1.8.2` · **Estado:** publicada.

- Corrige la revisión fijada de MADLAD-400 3B CT2 INT8.
- Corrige el tokenizer y los fixtures de integridad.
- Diferencia errores `404` de errores `401/403` de Hugging Face.

### 1.8.1 — Bootstrap local de uv y traducción local opcional

**Tipo:** `PATCH` · **Tag:** `v1.8.1` · **Estado:** publicada.

- Añade bootstrap gestionado de uv sin instalación global obligatoria.
- Permite preparar opcionalmente el modelo local durante el setup.
- Mantiene la descarga diferida mediante `manage_local_translation.py`.

### 1.8.0 — Recuperación de Whisper y traducción local

**Tipo:** `MINOR` · **Tag:** `v1.8.0` · **Estado:** publicada.

- Refina la recuperación selectiva de Whisper y separa VAD de la división de subtítulos.
- Incorpora MADLAD-400 3B CT2 INT8 como modelo local predeterminado y conserva OPUS-MT como alternativa ligera.
- Refuerza integridad, tokenización, revisiones fijadas y selección de modelos.

### 1.7.4 — Validación de shared vocabulary y migración a uv

**Tipo:** `PATCH` · **Estado:** publicada.

- Valida `shared_vocabulary.json` según la estructura real del artefacto fijado.
- Consolida la migración reproducible de desarrollo, CI, build y auditoría a uv.

### 1.7.3 — Metadatos del modelo local

**Tipo:** `PATCH` · **Estado:** publicada.

- Empaqueta los metadatos JSON necesarios para la revisión fijada del modelo local.

### 1.7.2 — Corrección de descarga del modelo local

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el límite y el recorrido de los artefactos del modelo local.

### 1.7.1 — Recuperación selectiva STT

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige el contrato de `clip_timestamps` de `faster-whisper`.

### 1.7.0 — Regeneración, Unicode y runtime de traducción

**Tipo:** `MINOR` · **Estado:** publicada.

- Consolida regeneración y manifests.
- Refuerza naming determinista, Unicode, límites de filesystem y colisiones.
- Consolida traducción local CTranslate2 + SentencePiece.

### 1.6.0 — Traducción local y endurecimiento GPU

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce traducción local opcional, recuperación STT configurable y runtime GPU gestionado.

### 1.5.1 — Endurecimiento ZIP y filesystem

**Tipo:** `PATCH` · **Estado:** publicada.

- Endurece traversal ZIP, rutas absolutas/UNC, symlinks, nombres reservados y colisiones Unicode/case.

### 1.5.0 — Whisper multiplataforma, contexto y packaging

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce wrappers multiplataforma, contexto externo de Whisper y empaquetado reproducible.

### 1.4.2 — Contrato CLI de regeneración

**Tipo:** `PATCH` · **Estado:** publicada.

- Amplía y documenta el contrato CLI de regeneración.

### 1.4.1 — Integración de regeneración en wrappers

**Tipo:** `PATCH` · **Estado:** publicada.

- Integra la regeneración en wrappers sin duplicar la lógica del pipeline.

### 1.4.0 — Regeneración limpia y endurecimiento de release

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce regeneración limpia, backup/restauración y endurecimiento de release.

### 1.3.0 — Concurrencia adaptativa segura

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce concurrencia adaptativa basada en CPU/RAM/GPU.

### 1.2.2 — Limpieza de timestamps de naming

**Tipo:** `PATCH` · **Estado:** publicada.

- Elimina timestamps técnicos de nombres y resultados.

### 1.2.1 — Corrección de instalación TTS

**Tipo:** `PATCH` · **Estado:** publicada.

- Corrige la instalación multiplataforma de recursos TTS.

### 1.2.0 — Mejoras de naming y TTS

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce naming descriptivo y bootstrap de assets Kokoro.

### 1.1.0 — Reparación VTT y TTS sincronizado

**Tipo:** `MINOR` · **Estado:** publicada.

- Introduce recuperación VTT, regeneración selectiva y TTS sincronizado.

### 1.0.1 — Instalación y mantenimiento

**Tipo:** `PATCH` · **Estado:** publicada.

- Añade y corrige documentación inicial de instalación.

### 1.0.0 — Primera release estable

Primera release estable de esta línea de producto.

## Release objetivo: 1.10.0

**Tipo:** `MINOR` · **Tag objetivo:** `v1.10.0` · **Estado:** no publicada.

La baseline de esta release es `v1.9.0` publicada.

### Cambios de producto

- Reparación conservadora de nombres ZIP UTF-8/CP437 y normalización NFC.
- Validación de traversal, rutas absolutas/UNC, symlinks, nombres reservados y colisiones.
- Separación entre carpetas visibles de `input`/`output` y estado privado de aplicación.
- Ampliación de la GUI existente para configuración, recuperación, deduplicación, diagnóstico, Whisper, traducción local, TTS y archivo de contexto.
- Motor Vosk específico para Windows x86/32 bits para mantener una ruta STT compatible con el build `win32`.
- Validación explícita de artefactos x64/x86 en Windows.
- Conservación de macOS x64 y Linux x86_64 como arquitecturas publicadas; no se anuncia soporte 32-bit donde la cadena actual no puede validarse de forma reproducible.

### Cambios de distribución

- Windows x64: `.exe` + `.msi`.
- Windows x86: `.exe` + `.msi` y wheel `win32`.
- macOS x64: `.app` dentro de `.zip`.
- Linux x86_64: AppImage.
- Los modelos y recursos grandes se mantienen fuera de los binarios cuando corresponde.

### CI/CD y calidad

- `uv lock --check` y sincronización bloqueada.
- `Ruff lint`, `Ruff security` y `Ruff format` sobre el árbol real del repositorio.
- Tests, `compileall`, `pip check`, auditoría de dependencias y packaging.
- Builds nativas para las arquitecturas que disponen de toolchain reproducible.
- Validación separada de Windows x86 con intérprete Python de 32 bits.

### Documentación y CLI

- Documentación operativa en español.
- Conservación de comandos, flags, rutas, APIs, formatos, nombres de modelos y nombres reales de las comprobaciones técnicas.
- `docs/CLI.md` conserva la semántica de los comandos públicos y utiliza `--help` como fuente de verdad para las opciones exactas.
- Historial completo de releases desde `1.0.0`, sin eliminar versiones anteriores.

### Validación obligatoria antes de publicar `v1.10.0`

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

Además, CI debe finalizar correctamente en todos los jobs requeridos de calidad, Release Gate, packaging y escritorio antes de crear el tag.

## Integridad histórica

Las versiones publicadas y sus títulos se conservan. Este documento puede normalizar idioma y estructura sin eliminar ni reescribir el alcance histórico de una release. Las releases candidatas/objetivo se distinguen de las publicadas.
