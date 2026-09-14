# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.8.2` → release PATCH publicada el 14 de septiembre de 2026; corrige el recurso MADLAD, tokenizer, fixtures y diagnóstico de descarga.
- `v1.8.1` → release PATCH publicada el 14 de septiembre de 2026; incorpora bootstrap gestionado de uv y preparación opt-in del modelo local.
- `v1.8.0` → release MINOR publicada el 13 de septiembre de 2026; consolida recuperación Whisper, modelos locales fijados y la base reproducible con uv.
- `v1.7.4` → release PATCH de validación del modelo local y migración reproducible a uv.
- `v1.7.3` → release PATCH de bootstrap de metadatos JSON del modelo local.
- `v1.7.2` → release PATCH de corrección del gestor de descarga del modelo local.
- `v1.7.1` → release PATCH de corrección de recuperación selectiva STT.
- `v1.7.0` → release MINOR de reprocessing, manifests, naming Unicode/filesystem y runtime de traducción local.
- `v1.6.0` → release MINOR de traducción local, recuperación STT configurable y endurecimiento GPU/runtime.
- `v1.5.1` → release PATCH de endurecimiento ZIP/filesystem multiplataforma.
- `v1.5.0` → release MINOR de wrappers multiplataforma, contexto Whisper y packaging.
- `v1.4.2` → release PATCH/MINOR histórica de contrato CLI de regeneración y help.
- `v1.4.1` → release PATCH de integración de wrappers de regeneración.
- `v1.4.0` → release MINOR de regeneración limpia y endurecimiento de release.
- `v1.3.0` → release MINOR de concurrencia adaptativa por recursos.
- `v1.2.2` → release PATCH de limpieza de timestamps en naming.
- `v1.2.1` → release PATCH de instalación TTS.
- `v1.2.0` → release MINOR de naming y mejoras TTS.
- `v1.1.0` → release MINOR de reparación VTT e integración TTS.
- `v1.0.1` → release PATCH de documentación de instalación y mantenimiento.
- `v1.0.0` → primera release estable.

Los tags publicados son historia inmutable y no deben modificarse, moverse ni reutilizarse.

## Release candidata actual: 1.8.3

`1.8.3` es una **PATCH** correctiva sobre la línea `1.8.x` y la única release actualmente no publicada.

Corrige una regresión introducida al hacer que `setup_env.*` pudiera instalar `uv` de forma gestionada por el proyecto: varios wrappers seguían exigiendo una instalación global en `PATH`, por lo que un entorno correctamente preparado podía fallar al ejecutar `run_local`, `setup_rclone`, `setup_google`, build o determinados modos unattended.

La corrección establece un contrato único:

1. `tools/uv/uv` en macOS/Linux, o `tools\\uv\\uv.exe` en Windows, cuando existe.
2. `uv`/`uv.exe` de `PATH` como fallback.
3. Solo `setup_env.*` instala una copia gestionada cuando ninguna existe.

Los wrappers comparten este contrato mediante `scripts/lib/resolve_uv.sh` y `scripts/lib/resolve_uv.bat` y ejecutan siempre el binario resuelto.

La regresión queda cubierta por `tests/test_uv_resolution_contract.py`.

## Límite de versión para la aplicación de escritorio

La aplicación de escritorio implementada en la rama de trabajo es una **funcionalidad nueva compatible hacia atrás** y, conforme a Semantic Versioning, no debe publicarse dentro de la candidata PATCH `1.8.3`.

Si la implementación de escritorio se incorpora a `main`, el siguiente release que la publique debe ser como mínimo `1.9.0` (salvo que se apruebe otro MINOR superior). En ese momento deben actualizarse de forma atómica `pyproject.toml`, `config/app.toml`, `uv.lock`, `CHANGELOG.md`, `docs/RELEASES.md`, `RELEASE_CANDIDATE.md`, `RELEASE_SCOPE.md` y la documentación relacionada.

Los binarios de escritorio tampoco convierten la release en una release móvil: el alcance móvil permanece fuera del producto hasta una decisión futura explícita.

## Integridad histórica

Las releases `1.8.0`, `1.8.1` y `1.8.2` son publicaciones oficiales. No deben describirse como candidatas, superseded candidates ni preparaciones inacabadas. Sus tags son inmutables.

La documentación de `1.8.3` debe añadirse como nueva candidata sin borrar ni sustituir el historial anterior.

## Trazabilidad de release

Cada release debe relacionar inequívocamente:

```text
source version
     ↓
CHANGELOG
     ↓
docs/RELEASES.md
     ↓
validated commit SHA
     ↓
tag vX.Y.Z
     ↓
GitHub Release
```

`v1.8.0`, `v1.8.1` y `v1.8.2` ya existen y permanecen inmutables. `v1.8.3` solo debe publicarse sobre el SHA exacto de `main` resultante de la validación final, después de CI y Release Gate verdes.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

## Política de dependencias

`pyproject.toml` es la única fuente declarativa de dependencias. `uv.lock` es la resolución reproducible y versionada. `uv lock --check` y los entornos `uv sync --locked` forman parte del Release Gate.
