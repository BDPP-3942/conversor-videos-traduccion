# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.7.0` → release publicada más reciente confirmada.
- `v1.6.0` → commit `a6cf0ee183a4802814fe0e061b4704e427166b85`.
- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

`v1.7.0`, `v1.6.0` y `v1.5.1` son historia publicada y no deben modificarse, moverse ni reutilizarse.

## 1.7.1 integrada

`1.7.1` es la corrección PATCH de recuperación selectiva STT ya integrada en `main`. Su estado debe conservarse como baseline funcional del nuevo cambio; si todavía no se ha creado su tag/release, debe hacerse sobre el SHA exacto del merge antes de considerar publicada esa release.

## Candidata 1.7.2

La candidata actual es una corrección PATCH sobre el estado funcional `1.7.1`:

- Corrige el cálculo del límite de descarga del modelo de traducción local.
- Evita el `KeyError: 'model.bin'` provocado por la evaluación eager del argumento por defecto de `dict.get`.
- Mantiene la descarga del modelo fijado, su validación de integridad y la inicialización offline del proveedor.
- Añade regresiones para descarga completa y llamada del proveedor tras preparar el modelo.
- No cambia el contrato público de configuración ni las versiones de dependencias.
- Debe terminar en un único SHA validado por CI y Release Gate.
- Solo después del merge se crea el tag inmutable `v1.7.2` sobre el SHA exacto resultante de `main`.

`1.7.0` y `1.6.0` permanecen como antecedentes históricos; `1.7.1` es el baseline funcional inmediato de esta candidata.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La corrección de `1.7.2` no cambia contratos públicos ni añade funcionalidad incompatible, por lo que `PATCH` es la clasificación adecuada.

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
