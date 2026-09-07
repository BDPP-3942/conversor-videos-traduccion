# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.7.0` → release publicada más reciente.
- `v1.6.0` → commit `a6cf0ee183a4802814fe0e061b4704e427166b85`.
- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

`v1.7.0`, `v1.6.0` y `v1.5.1` son historia publicada y no deben modificarse, moverse ni reutilizarse.

## Candidata 1.7.1

La candidata actual es una corrección PATCH sobre la **release publicada más reciente `v1.7.0`**:

- Corrige el contrato de `clip_timestamps` en la recuperación selectiva de `faster-whisper`.
- Mantiene las funcionalidades y endurecimientos introducidos hasta `1.7.0`, incluyendo reprocessing/manifests, naming Unicode/filesystem y runtime de traducción local.
- Fija el stack compatible de `faster-whisper`/CTranslate2 mediante `pyproject.toml` y `requirements.txt`.
- Debe terminar en un único SHA validado por CI y Release Gate.
- Solo después del merge se crea el tag inmutable `v1.7.1` sobre el SHA exacto resultante de `main`.

`1.5.1` y `1.6.0` permanecen como antecedentes históricos. `1.7.0` es la release previa inmediata y el baseline funcional correcto para revisar esta candidata.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La corrección de `1.7.1` no cambia contratos públicos ni añade funcionalidad de producto incompatible, por lo que `PATCH` es la clasificación adecuada.

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

No se crean tags retrospectivos ni se reasignan tags publicados.

## Historial de reconstrucción

El repositorio conserva documentación histórica de etapas de reconstrucción anteriores (`4.x`/`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
