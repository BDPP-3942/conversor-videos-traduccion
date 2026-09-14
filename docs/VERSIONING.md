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

## Release candidata: 1.8.2

La candidata actual es `1.8.2`, una **PATCH** correctiva sobre la release publicada `1.8.0`. La preparación `1.8.1` queda supersedida y no se considera una release publicada.

El incremento PATCH está justificado por la corrección del recurso MADLAD y por ajustes compatibles de validación, tests, CI y documentación:

- pinning de `cstr/madlad400-3b-ct2-int8` a la revisión `fd0b55729c074372eb84b52b9309a00dc65c40c4`;
- uso del tokenizer real `spiece.model` del artefacto fijado;
- validación reproducible mediante tamaño y SHA-256 del tokenizer y del modelo;
- diagnóstico diferenciado entre artefactos/revisiones inexistentes (404) y autenticación/autorización (401/403);
- corrección de fixtures de tests para que sus tamaños esperados coincidan con los bytes realmente escritos;
- alineación de metadatos de versión, documentación de release y controles de calidad con `1.8.2`.

No se cambia el contrato público de procesamiento, almacenamiento o CLI.

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

`v1.8.0` ya existe y no debe recrearse ni moverse. `v1.8.2` solo debe publicarse sobre el SHA exacto de `main` resultante del merge de la candidata, después de que CI y Release Gate sean verdes.

## Política de dependencias

`pyproject.toml` es la única fuente declarativa de dependencias. `uv.lock` es la resolución reproducible y versionada. `uv lock --check` y los entornos `uv sync --locked` forman parte del Release Gate.

La auditoría utiliza el grupo `audit`. Antes de ejecutar `pip-audit`, CI elimina el paquete editable local para que la auditoría se concentre en dependencias resolubles desde PyPI y no falle por el propio proyecto local.

## Historial de reconstrucción

El repositorio conserva documentación histórica de etapas de reconstrucción anteriores (`4.x`/`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
