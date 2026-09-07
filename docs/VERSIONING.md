# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.7.2` → release PATCH publicada con la corrección del gestor de descarga del modelo local.
- `v1.7.0` → release publicada anterior en la línea 1.x.
- `v1.6.0` → commit `a6cf0ee183a4802814fe0e061b4704e427166b85`.
- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

Los tags publicados son historia inmutable y no deben modificarse, moverse ni reutilizarse.

## Candidata 1.7.3

La candidata actual es una corrección PATCH sobre el estado publicado `1.7.2`:

- Distribuye `config.json` y `tokenizer_config.json` del modelo local fijado junto al paquete Python.
- Instala esos metadatos en el directorio gestionado antes de inicializar CTranslate2.
- Mantiene `shared_vocabulary.json`, `model.bin`, `source.spm` y `target.spm` como artefactos descargados y validados.
- Añade regresiones para los metadatos empaquetados y para la preparación completa del proveedor.
- No cambia el contrato público de configuración ni las versiones de dependencias.
- Debe terminar en un único SHA validado por CI y Release Gate.
- Solo después del merge se crea el tag inmutable `v1.7.3` sobre el SHA exacto resultante de `main`.

`1.7.1` y `1.7.2` permanecen como antecedentes funcionales inmediatos y sus tags publicados no deben modificarse.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La corrección de `1.7.3` no cambia contratos públicos ni añade funcionalidad incompatible, por lo que `PATCH` es la clasificación adecuada.

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
