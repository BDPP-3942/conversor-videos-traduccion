# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Release candidata actual: 1.8.3

`1.8.3` es una **PATCH** correctiva sobre la línea `1.8.x`. Corrige una regresión introducida al hacer que `setup_env.*` pudiera instalar `uv` de forma gestionada por el proyecto: varios wrappers seguían exigiendo una instalación global en `PATH`, por lo que un entorno correctamente preparado podía fallar al ejecutar `run_local`, `setup_rclone`, `setup_google`, build o determinados modos unattended.

La corrección establece un contrato único:

1. `tools/uv/uv` en macOS/Linux, o `tools\\uv\\uv.exe` en Windows, cuando existe.
2. `uv`/`uv.exe` de `PATH` como fallback.
3. Solo `setup_env.*` instala una copia gestionada cuando ninguna existe.

Los wrappers comparten este contrato mediante `scripts/lib/resolve_uv.sh` y `scripts/lib/resolve_uv.bat` y ejecutan siempre el binario resuelto.

La regresión queda cubierta por `tests/test_uv_resolution_contract.py`, incluyendo los wrappers POSIX y Windows, los scripts de build y los modos unattended.

## Releases publicadas / históricas

- `v1.8.0` → release MINOR publicada el 13 de septiembre de 2026.
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

`v1.8.0` permanece inmutable. `v1.8.3` solo debe publicarse sobre el SHA exacto de `main` resultante del merge de esta candidata después de CI y Release Gate verdes.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

## Política de dependencias

`pyproject.toml` es la única fuente declarativa de dependencias. `uv.lock` es la resolución reproducible y versionada. `uv lock --check` y los entornos `uv sync --locked` forman parte del Release Gate.
