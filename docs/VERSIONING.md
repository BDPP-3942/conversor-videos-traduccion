# Versionado

La línea de releases de producto actualmente publicada es `1.x`.

## Releases publicadas

- `v1.7.2` → release PATCH publicada con la corrección del gestor de descarga del modelo local.
- `v1.7.1` y `v1.7.0` → releases anteriores de la línea 1.x documentadas en `docs/RELEASES.md`.
- `v1.6.0` → commit `a6cf0ee183a4802814fe0e061b4704e427166b85`.
- `v1.5.1` → commit `06ee8d265b57214596f079f3bb426b9b27042b1e`.

Los tags publicados son historia inmutable y no deben modificarse, moverse ni reutilizarse.

## Candidata 1.7.4

La candidata actual es una corrección PATCH sobre el estado publicado `1.7.2`. Agrupa las correcciones de mantenimiento ya integradas en `1.7.3` y `1.7.4` con la migración de infraestructura a `uv`:

- Corrige la validación de `shared_vocabulary.json` para aceptar la estructura real del artefacto fijado.
- Conserva el bootstrap de metadatos JSON empaquetados del modelo local.
- Migra la gestión de dependencias de desarrollo, CI, build y auditoría a `uv`.
- Versiona `uv.lock` como resolución reproducible del grafo de dependencias.
- Mantiene `pip` como mecanismo de compatibilidad para validar e instalar el wheel publicado.
- Ejecuta `pip-audit` desde el grupo de auditoría gestionado por `uv`.
- Debe terminar en un único SHA validado por CI y Release Gate.
- Solo después del merge se crea el tag inmutable `v1.7.4` sobre el SHA exacto resultante de `main`.

`1.7.1`, `1.7.2` y los antecedentes anteriores permanecen como historia funcional y sus tags publicados no deben modificarse.

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: cambio incompatible de CLI, configuración, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La candidata `1.7.4` no introduce una arquitectura incompatible ni cambia contratos públicos de la aplicación; la migración a `uv` afecta al desarrollo, CI y packaging reproducible, manteniendo compatibilidad de instalación del wheel mediante `pip`. Por tanto, `PATCH` es la clasificación adecuada.

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

## Política de lockfile

`pyproject.toml` es la única fuente declarativa de dependencias del proyecto. `uv.lock` es la resolución versionada y reproducible utilizada por CI y desarrollo. Una release no se considera validada mientras `uv lock --check` no pase sobre el SHA candidato exacto.

La auditoría de dependencias se declara en el grupo `audit` y se ejecuta con `uv run --locked --group audit pip-audit --strict`; no se depende de una instalación global o accidental de `pip-audit`.

## Historial de reconstrucción

El repositorio conserva documentación histórica de etapas de reconstrucción anteriores (`4.x`/`5.x`) para trazabilidad. Esa historia no constituye la línea actual de releases de producto y no debe usarse para alterar la secuencia `1.x`.
