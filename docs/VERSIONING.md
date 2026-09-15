# Versionado

La línea de releases de producto es `1.x` y utiliza Semantic Versioning.

## Releases publicadas

- `v1.9.0` — MINOR: aplicación GUI de escritorio y distribución nativa en runners de cada plataforma.
- `v1.8.3` — PATCH: resolución gestionada de `uv` en wrappers POSIX y Windows.
- `v1.8.2` — PATCH: corrección de la revisión MADLAD, tokenizer, fixtures e información de diagnóstico de Hugging Face.
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

## Release candidate: 1.10.0

`1.10.0` es una **MINOR** porque añade funcionalidad compatible sobre la baseline publicada `v1.9.0`. La creación de la GUI y la distribución nativa pertenecen a `v1.9.0` y no deben volver a registrarse como funcionalidad nueva de `1.10.0`.

### Cambios registrados en 1.10.0

1. **Reparación ZIP/Unicode:** reparación conservadora de nombres cuyos bytes UTF-8 fueron interpretados como CP437 cuando falta el indicador UTF-8, preservando nombres CP437 legítimos.
2. **Normalización Unicode:** canonicalización NFC antes de tocar el filesystem y detección de colisiones por normalización y mayúsculas/minúsculas.
3. **Almacenamiento:** separación entre las carpetas visibles de `input`/`output` y el estado privado de la aplicación; los valores predeterminados pasan a `Documentos/Video Translation Pipeline/input` y `output`.
4. **Estado privado:** logs, manifests, cachés, trabajo intermedio y fallos dejan de depender de la carpeta de instalación.
5. **GUI existente:** ampliación de la interfaz de `v1.9.0` para exponer configuración adicional de Whisper, FFmpeg, traducción local, TTS y archivo de contexto, además de diagnóstico y recuperación.
6. **Windows:** endurecimiento del contrato de instalación para distinguir correctamente builds x64 y x86 y mantener la instalación x64 en el `Program Files` nativo.
7. **CLI:** ampliación y alineación de las opciones públicas de ejecución, regeneración, recuperación y TTS con sus parsers reales.
8. **Documentación:** traducción de la documentación operativa al español, preservando terminología técnica establecida, comentarios históricos y referencias mediante enlaces relativos.
9. **CI/CD:** automatización segura de la sincronización de `uv.lock` mediante PR auxiliar cuando es necesaria, sin escritura directa sobre una rama protegida.

## Baseline y trazabilidad

La baseline de `1.10.0` es **`v1.9.0` publicada**. El alcance de esta release se obtiene comparando `v1.9.0` con el SHA final candidato; no se deben copiar cambios de releases anteriores a la sección de `1.10.0`.

Antes de publicar `v1.10.0`, deben estar sincronizados `pyproject.toml`, `config/app.toml`, `uv.lock`, `CHANGELOG.md`, `docs/RELEASES.md`, `docs/VERSIONING.md` y los documentos de preparación de release.

## Política de dependencias

`pyproject.toml` es la fuente declarativa. `uv.lock` es la resolución reproducible versionada y debe estar sincronizada con cada versión publicada. `uv lock --check` y `uv sync --locked` forman parte del Release Gate.

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

La release automática de escritorio se ejecuta desde [`.github/workflows/release.yml`](../.github/workflows/release.yml) cuando se crea un tag `vX.Y.Z`. El workflow construye los artefactos en runners nativos y los adjunta al GitHub Release. No se deben subir manualmente binarios generados desde un equipo de desarrollo.

## Reglas documentales y de CLI

- La documentación operativa nueva o modificada se redacta en español.
- Los comentarios y docstrings de código se redactan en español cuando contienen texto humano. Nombres técnicos, APIs, flags, claves, clases, funciones y directivas del lenguaje se conservan literalmente cuando forman parte del contrato.
- Todas las descripciones `description=` y `help=` de `argparse` deben estar en español.
- `docs/CLI.md` debe incluir los casos de uso públicos y reflejar la salida real de `--help`.
- Las referencias a otros documentos deben ser enlaces Markdown relativos.
- Los comentarios históricos no se eliminan al reorganizar o traducir documentación.
- Estas reglas se aplican directamente a los ficheros canónicos y no dependen de un índice auxiliar.

## Semantic Versioning

- **MAJOR:** cambios incompatibles de CLI, configuración, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.
