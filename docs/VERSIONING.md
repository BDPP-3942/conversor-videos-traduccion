# Versionado

La línea de releases de producto es `1.x` y utiliza Semantic Versioning.

## Releases publicadas

- `v1.9.0` — MINOR: aplicación GUI de escritorio y distribución nativa.
- `v1.8.3` — PATCH: resolución gestionada de `uv` en wrappers POSIX y Windows.
- `v1.8.2` — PATCH: corrección de revisión MADLAD, tokenizer, fixtures y diagnósticos de Hugging Face.
- `v1.8.1` — PATCH: bootstrap gestionado de uv y preparación opt-in de traducción local.
- `v1.8.0` — MINOR: recuperación Whisper refinada, modelos locales fijados y base reproducible con uv.
- `v1.7.4` — PATCH: validación de `shared_vocabulary.json` y migración reproducible a uv.
- `v1.7.3` — PATCH: bootstrap de metadatos JSON del modelo local.
- `v1.7.2` — PATCH: corrección de descarga del modelo local.
- `v1.7.1` — PATCH: compatibilidad de recuperación selectiva STT con `clip_timestamps`.
- `v1.7.0` — MINOR: reprocessing, manifests, naming Unicode/filesystem y runtime de traducción local.
- `v1.6.0` — MINOR: traducción local, recuperación STT configurable y endurecimiento GPU/runtime.
- `v1.5.1` — PATCH: endurecimiento ZIP/filesystem multiplataforma.
- `v1.5.0` — MINOR: wrappers multiplataforma, contexto Whisper y packaging.
- `v1.4.2` — PATCH: contrato CLI y help de regeneración.
- `v1.4.1` — PATCH: integración de regeneración en wrappers.
- `v1.4.0` — MINOR: regeneración limpia y endurecimiento de release.
- `v1.3.0` — MINOR: concurrencia adaptativa por recursos.
- `v1.2.2` — PATCH: limpieza de timestamps en naming.
- `v1.2.1` — PATCH: instalación multiplataforma de recursos TTS.
- `v1.2.0` — MINOR: naming descriptivo y bootstrap TTS.
- `v1.1.0` — MINOR: reparación VTT y TTS sincronizado.
- `v1.0.1` — PATCH: documentación inicial de instalación y mantenimiento.
- `v1.0.0` — primera release estable.

Los tags publicados son historia inmutable y no deben reutilizarse ni reclasificarse.

## Release objetivo: 1.10.0

`1.10.0` es una **MINOR** sobre la baseline publicada `v1.9.0`. La funcionalidad GUI y la distribución nativa pertenecen a `v1.9.0`; esta release no las vuelve a presentar como funcionalidad nueva.

### Cambios de 1.10.0

1. **ZIP/Unicode:** reparación conservadora de nombres cuyos bytes UTF-8 fueron interpretados como CP437 cuando falta el indicador UTF-8, preservando nombres CP437 legítimos.
2. **Normalización Unicode:** canonicalización NFC antes de acceder al filesystem y detección de colisiones por normalización y mayúsculas/minúsculas.
3. **Almacenamiento:** separación entre `input`/`output` visibles y el estado privado de la aplicación, con valores predeterminados bajo `Documents/Video Translation Pipeline/`.
4. **Estado privado:** logs, manifests, cachés, trabajo intermedio y fallos dejan de depender de la carpeta de instalación.
5. **GUI:** ampliación de la interfaz existente para exponer configuración de Whisper, FFmpeg, traducción local, TTS, contexto, diagnóstico, recuperación y deduplicación.
6. **Windows:** distinción explícita entre builds x64 y x86 y uso de la ubicación nativa de `Program Files` para x64.
7. **STT x86:** motor Vosk específico para Windows de 32 bits y artefactos `win32` construidos con un intérprete Python x86 real.
8. **CLI:** ampliación y alineación de la documentación de ejecución, regeneración, recuperación, proveedores y TTS con sus parsers reales.
9. **Documentación:** documentación operativa en español, preservando nombres técnicos, comandos, rutas, APIs y terminología contractual.
10. **CI/CD:** validación de lockfile, lint, security, format, tests, packaging, auditoría de dependencias y artefactos de escritorio sobre las arquitecturas realmente disponibles.

### Baseline y trazabilidad

La baseline de `1.10.0` es **`v1.9.0` publicada**. El alcance se obtiene comparando `v1.9.0` con el SHA final candidato. No se copian cambios de releases anteriores a la sección de `1.10.0`.

Antes de crear `v1.10.0` deben estar sincronizados `pyproject.toml`, `config/app.toml`, `uv.lock`, `CHANGELOG.md`, `docs/RELEASES.md`, `docs/VERSIONING.md` y los documentos de preparación de release.

## Política de dependencias

`pyproject.toml` es la fuente declarativa. `uv.lock` es la resolución reproducible versionada. `uv lock --check` y `uv sync --locked` forman parte del Release Gate.

## Trazabilidad

```text
pyproject.toml / config/app.toml
          ↓
      uv.lock
          ↓
     CHANGELOG.md
          ↓
  docs/RELEASES.md
          ↓
 Release Gate + CI
          ↓
   validated main SHA
          ↓
       tag vX.Y.Z
          ↓
 GitHub Release + desktop artifacts
```

La release automática de escritorio se ejecuta desde [`.github/workflows/release.yml`](../.github/workflows/release.yml) al crear un tag `vX.Y.Z`. Los artefactos se construyen en runners de la arquitectura correspondiente y se adjuntan al GitHub Release.

## Reglas documentales y de CLI

- La documentación operativa nueva o modificada se redacta en español.
- Los comentarios y docstrings con texto humano se redactan en español.
- Nombres técnicos, APIs, flags, claves, clases, funciones, rutas, formatos y directivas se conservan literalmente cuando forman parte del contrato.
- Todas las descripciones `description=` y `help=` de `argparse` deben estar en español.
- `docs/CLI.md` debe cubrir los casos de uso públicos y conservar detalle semántico aunque las opciones concretas también aparezcan en `--help`.
- Las referencias a otros documentos deben ser enlaces Markdown relativos.
- Los comentarios históricos no se eliminan al reorganizar o traducir documentación.
- Las comprobaciones técnicas conservan sus nombres reales: `Ruff lint`, `Ruff security`, `Ruff format`, `uv lock --check`, `uv sync --locked`, etc.

## Semantic Versioning

- **MAJOR:** cambios incompatibles de CLI, configuración, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.
