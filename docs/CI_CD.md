# CI/CD

GitHub Actions valida los cambios sobre `main` y las pull requests y, para releases etiquetadas, construye automáticamente los artefactos de escritorio.

## Quality

El job de calidad ejecuta:

- `uv lock --check`;
- `uv sync --locked`;
- `uv pip check`;
- Ruff lint, imports y format;
- `compileall`.

## Tests

La matriz conserva Linux, Windows y macOS con Python 3.11, 3.12 y 3.13. Esto es obligatorio porque filesystem, procesos, librerías nativas y normalización de rutas no se pueden demostrar en un único sistema.

## Packaging

El packaging Python valida `uv build`, recursos, instalación limpia con pip y entry points.

El workflow `.github/workflows/desktop.yml` añade packaging nativo para la GUI:

- Ubuntu: PyInstaller + AppDir + AppImage.
- Windows: PyInstaller + WiX 6.0.2, produciendo `.exe` y `.msi`.
- macOS: PyInstaller `BUNDLE`, produciendo `.app`.

Cada plataforma valida la existencia del artefacto esperado y lo publica como workflow artifact.

## Linux desktop packaging

Linux no utiliza un framework GUI distinto. `src.desktop` se empaqueta con PyInstaller como en los otros sistemas. `scripts/build_desktop.py` crea un AppDir con `AppRun`, `.desktop` e icono SVG y `appimagetool` genera el AppImage x86_64.

Esto permite una aplicación Linux portable sin exigir una distribución concreta ni un instalador de paquetes del sistema.

## Release automation

`.github/workflows/release.yml` se activa al crear `vX.Y.Z` o manualmente para un tag existente.

El workflow:

1. hace checkout del tag exacto;
2. ejecuta `uv lock --check` y `uv sync --locked`;
3. construye Windows, macOS y Linux en runners nativos;
4. valida los artefactos;
5. comprime el `.app` de macOS;
6. publica los tres binarios como assets de workflow;
7. crea la GitHub Release si no existe o hace upload con `--clobber` si ya existe.

GitHub sigue generando automáticamente los ZIP/TAR de código fuente para el tag. La release final contiene, por tanto, tanto los fuentes automáticos como los binarios nativos sin intervención manual.

Artefactos esperados:

```text
VideoTranslationPipeline-X.Y.Z-linux-x86_64.AppImage
VideoTranslationPipeline-X.Y.Z-windows-x64.msi
VideoTranslationPipeline-X.Y.Z-macos.app.zip
```

El `.exe` se valida durante el job Windows y permanece dentro del paquete generado por PyInstaller; si se desea distribuirlo además como asset independiente, se puede añadir al patrón de upload sin cambiar la arquitectura.

## Versionado y lockfile

`pyproject.toml` es la fuente declarativa y `uv.lock` la resolución reproducible. Cada release debe sincronizar ambos.

La rama de preparación de `1.9.0` incluye un workflow de sincronización de metadatos que regenera `uv.lock` cuando cambia `pyproject.toml` y actualiza el encabezado de `CHANGELOG.md`. En el release final, el requisito sigue siendo `uv lock --check` sobre el SHA etiquetado.

## Release 1.9.0

`1.9.0` es MINOR porque introduce la aplicación GUI y la distribución nativa. El cambio no elimina CLI, scheduling, unattended execution ni los entry points existentes.

El Release Gate final debe comprobar el SHA exacto de `main`, matriz de tests, Ruff, seguridad, compileall, lockfile, packaging y los artefactos nativos de Linux/Windows/macOS.

## uv policy

Para scripts de checkout, el contrato sigue siendo:

1. `tools/uv/uv` en POSIX o `tools\\uv\\uv.exe` en Windows;
2. `uv`/`uv.exe` de `PATH` como fallback;
3. solo los wrappers de setup hacen bootstrap de una copia gestionada si no existe ninguna.

Los wrappers consumen `scripts/lib/resolve_uv.sh` y `scripts/lib/resolve_uv.bat`.

## Local parity

```bash
uv lock --check
uv sync --locked --extra google --group dev
uv pip check
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall .
uv build
```

Para validar desktop localmente:

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format native
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format linux-appimage
```

El segundo comando requiere Linux y `appimagetool`; WiX requiere Windows. La firma/notarización de macOS y firma de editor de Windows son operaciones de publicación y requieren credenciales específicas.
