# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.7.4` → release PATCH publicada el 8 de septiembre de 2026; corrige la validación de `shared_vocabulary.json` del modelo de traducción local.
- `v1.7.3` → release PATCH de bootstrap de metadatos JSON del modelo local.
- `v1.7.2` → release PATCH de corrección del gestor de descarga del modelo local.
- `v1.7.1` → release PATCH de corrección de recuperación selectiva STT.
- `v1.7.0` → release MINOR de reprocessing, manifests, naming Unicode/filesystem y runtime de traducción local.
- `v1.6.0` → commit `a6cf0ee183a4802814fe0e061b4704e427166b85`.
- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

Los tags publicados son historia inmutable y no deben modificarse, moverse ni reutilizarse.

## Próxima release: 1.8.0

La próxima release prevista es `1.8.0`, una **MINOR** compatible sobre la release publicada `1.7.4`.

El incremento MINOR está justificado por funcionalidad nueva compatible:

- separación entre silencio VAD y separación de subtítulos de Whisper;
- recuperación STT sospechosa sin prompt ni contexto previo;
- conservación de `clip_timestamps` numérico durante la recuperación selectiva;
- incorporación de MADLAD-400 3B CT2 INT8 como modelo local predeterminado sin eliminar OPUS-MT;
- soporte explícito de dos modelos locales con configuraciones, revisiones y tokenizadores independientes;
- límite de instalación e integridad de los modelos locales;
- gestión reproducible de dependencias de desarrollo/CI/build mediante `uv`.

No se requiere `1.7.5` para este conjunto: `1.7.4` ya está publicada y el alcance combinado de PR #42 + PR #45 contiene cambios funcionales que corresponden a MINOR.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

## Trazabilidad

Cada release debe poder relacionar inequívocamente:

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

`v1.7.4` ya existe y no debe recrearse ni moverse. `v1.8.0` solo debe etiquetarse sobre el SHA exacto de `main` que haya pasado CI y Release Gate después de integrar todos los cambios de la release.

## Política de dependencias

`pyproject.toml` es la única fuente declarativa de dependencias. `uv.lock` es la resolución reproducible y versionada. `uv lock --check` y los entornos `uv sync --locked` forman parte del Release Gate.

La auditoría utiliza el grupo `audit`. Antes de ejecutar `pip-audit`, CI elimina el paquete editable local para que la auditoría se concentre en dependencias resolubles desde PyPI y no falle por el propio proyecto local.

## Historial de reconstrucción

El repositorio conserva documentación histórica de etapas de reconstrucción anteriores (`4.x`/`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
