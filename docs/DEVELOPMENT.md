# Guía de desarrollo

## Entorno

El rango de Python compatible es `>=3.11,<3.14`.

El proyecto utiliza `uv` para reproducir el entorno de desarrollo:

```bash
uv sync --locked --group dev
```

Los extras opcionales se instalan solo cuando la funcionalidad que se esté desarrollando los necesita, por ejemplo `google` o `tts`:

```bash
uv sync --locked --extra google --group dev
uv sync --locked --extra tts --group dev
```

## Estructura del proyecto

```text
config/       carga de configuración y ajustes
src/          módulos de la aplicación y adaptadores
tests/        pruebas automatizadas
scripts/      utilidades de configuración, ejecución, programación y empaquetado
docs/         documentación técnica
storage/      directorios de runtime para entrada/salida/estado
tools/        recursos externos de runtime
```

## Flujo de cambios

1. Identifica la abstracción existente del pipeline responsable del cambio.
2. Evita duplicar la lógica de negocio de proveedores/almacenamiento en los wrappers.
3. Actualiza la configuración/CLI solo cuando la implementación exponga realmente el cambio.
4. Añade pruebas deterministas.
5. Actualiza la documentación canónica.
6. Ejecuta las comprobaciones de calidad locales e inspecciona la CI.
7. Si el cambio se publica, regístralo en `CHANGELOG.md` y `docs/RELEASES.md` con evidencias vinculadas a la release/tag.

## Regla de documentación

No documentes una opción, comando, ruta o funcionalidad salvo que pueda verificarse contra el código, la configuración o las pruebas actuales. Prioriza la salida de `--help` y las definiciones del código fuente frente a la documentación histórica.

Los comandos de herramientas se mantienen con su sintaxis real. No se traducen nombres de comandos, flags, rutas, dependencias ni APIs: por ejemplo, `uv run ruff check .`, `uv run pytest -q` y `uv build` deben conservarse literalmente.
