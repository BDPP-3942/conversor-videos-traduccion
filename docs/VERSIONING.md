# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.8.0` → release MINOR publicada el 13 de septiembre de 2026; consolida recuperación Whisper, modelos locales fijados y la base reproducible con uv.
- `v1.7.4` → release PATCH publicada el 8 de septiembre de 2026; corrige la validación de `shared_vocabulary.json` del modelo de traducción local.
- `v1.7.3` → release PATCH de bootstrap de metadatos JSON del modelo local.
- `v1.7.2` → release PATCH de corrección del gestor de descarga del modelo local.
- `v1.7.1` → release PATCH de corrección de recuperación selectiva STT.
- `v1.7.0` → release MINOR de reprocessing, manifests, naming Unicode/filesystem y runtime de traducción local.
- `v1.6.0` → release MINOR de traducción local, recuperación STT configurable y endurecimiento GPU/runtime.
- `v1.5.1` → release PATCH de endurecimiento ZIP/filesystem multiplataforma.
- `v1.5.0` → release MINOR de wrappers multiplataforma, contexto Whisper y packaging.
- `v1.4.2` → release MINOR de contrato CLI de regeneración y alineación del help.
- `v1.4.1` → release PATCH de integración de wrappers de regeneración.
- `v1.4.0` → release MINOR de regeneración limpia y endurecimiento de release.
- `v1.3.0` → release MINOR de concurrencia adaptativa por recursos.
- `v1.2.2` → release PATCH de limpieza de timestamps en naming.
- `v1.2.1` → release PATCH de instalación de recursos TTS.
- `v1.2.0` → release MINOR de naming y mejoras TTS.
- `v1.1.0` → release MINOR de reparación VTT e integración TTS.
- `v1.0.1` → release PATCH de documentación de instalación y mantenimiento.
- `v1.0.0` → primera release estable de la línea de producto.

Los tags publicados son historia inmutable y no deben modificarse, moverse ni reutilizarse.

## Release candidata: 1.8.1

La candidata actual es `1.8.1`, una **PATCH** compatible sobre la release publicada `1.8.0`.

El incremento PATCH está justificado por mejoras de instalación, bootstrap y documentación sin cambios incompatibles de CLI, configuración, formatos o arquitectura de procesamiento:

- bootstrap automático de una copia de uv bajo `tools/uv/` cuando no existe uv en `PATH`;
- reutilización de una copia ya instalada en `tools/uv/` y preferencia por uv del sistema cuando está disponible;
- soporte equivalente del bootstrap local en macOS/Linux y Windows;
- nueva opción `--local-translation` para preparar durante el setup el modelo local fijado;
- conservación del comando independiente `uv run python scripts/manage_local_translation.py download` para instalaciones diferidas;
- documentación de la nueva secuencia de instalación y de la separación entre entorno Python y pesos de modelos.

No se cambia el modelo local predeterminado, las revisiones fijadas, la cadena de proveedores, el runtime GPU ni el contrato de los datos procesados.

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

`v1.8.0` ya existe y no debe recrearse ni moverse. `v1.8.1` solo debe publicarse sobre el SHA exacto de `main` resultante del merge de la candidata, después de que CI y Release Gate sean verdes.

## Política de dependencias

`pyproject.toml` es la única fuente declarativa de dependencias. `uv.lock` es la resolución reproducible y versionada. `uv lock --check` y los entornos `uv sync --locked` forman parte del Release Gate.

La auditoría utiliza el grupo `audit`. Antes de ejecutar `pip-audit`, CI elimina el paquete editable local para que la auditoría se concentre en dependencias resolubles desde PyPI y no falle por el propio proyecto local.

## Historial de reconstrucción

El repositorio conserva documentación histórica de etapas de reconstrucción anteriores (`4.x`/`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
