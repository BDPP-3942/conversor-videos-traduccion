# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.3.0` → commit `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`.

`v1.3.0` es historia publicada y no debe modificarse, moverse ni reutilizarse.

## Candidata 1.4.0

La evolución posterior a `v1.3.0` se agrupa en una nueva release coherente:

- PR #24: regeneración limpia explícita desde la fuente mediante `MediaPipeline`.
- PR #25: gobernanza e higiene del repositorio.
- Hardening adicional solo cuando exista evidencia y regresión asociada.

La candidata debe terminar en un único SHA validado. Solo después se crea el tag inmutable `v1.4.0` sobre ese SHA.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La regeneración limpia es una operación nueva y explícita, compatible con la ejecución normal, por lo que `1.4.0` es semánticamente apropiado salvo que la auditoría detecte un cambio incompatible.

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

El repositorio conserva documentación histórica de una etapa de reconstrucción anterior (`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
