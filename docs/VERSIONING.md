# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

`v1.5.1` es historia publicada y no debe modificarse, moverse ni reutilizarse.

## Candidata 1.6.1

La candidata actual es una corrección PATCH compatible con la línea `1.6.x`:

- Corrige el contrato de `clip_timestamps` en la recuperación selectiva de `faster-whisper`.
- Mantiene el pipeline audiovisual, la configuración pública de recuperación y los formatos de salida.
- Fija el stack compatible de `faster-whisper`/CTranslate2 mediante `pyproject.toml` y `requirements.txt`.
- Debe terminar en un único SHA validado por CI y Release Gate.
- Solo después del merge se crea el tag inmutable `v1.6.1` sobre el SHA exacto resultante de `main`.

La candidata anterior `1.6.0` queda documentada como la línea funcional que introdujo traducción local, endurecimiento GPU/runtime y recuperación STT configurable; no debe crearse `v1.6.0` desde esta rama de corrección.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La corrección de `1.6.1` no cambia contratos públicos ni añade funcionalidad de producto incompatible, por lo que `PATCH` es la clasificación adecuada.

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
