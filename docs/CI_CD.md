# CI/CD

GitHub Actions valida los cambios sobre `main` y las pull requests y, para releases etiquetadas, construye automáticamente los artefactos de escritorio.

## Quality

El job de calidad ejecuta:

- `uv lock --check`;
- `uv sync --locked`;
- `uv pip check`;
- Ruff lint, imports, security y format;
- `compileall`.

La configuración de Ruff no se relaja para ocultar hallazgos de seguridad: si aparece una alerta `S*`, se corrige el código que la provoca.

## Tests

La matriz conserva Linux, Windows y macOS con Python 3.11, 3.12 y 3.13. Esto es obligatorio porque filesystem, procesos, librerías nativas y normalización de rutas no se pueden demostrar en un único sistema.

## Packaging

El packaging Python valida `uv build`, recursos, instalación limpia con pip y entry points.

El workflow `.github/workflows/desktop.yml` añade packaging nativo para la GUI:

- Ubuntu: PyInstaller + AppDir + AppImage x86_64.
- Windows x64: PyInstaller + WiX 6.0.2, produciendo `.exe`, MSI x64 y ZIP portable x64.
- macOS: PyInstaller `BUNDLE`, produciendo `.app`.

La arquitectura Windows no se deduce del sistema operativo de forma abstracta: el ejecutable y sus dependencias deben ser realmente de la arquitectura solicitada. El build valida que la arquitectura del intérprete Python coincide con `--windows-arch`.

Actualmente no se publica una build Windows x86. La comprobación realizada con Python x86 demuestra que `ctranslate2==4.8.2`, dependencia del runtime actual, no dispone de wheel `win32`; `uv sync --locked` falla antes de poder construir el ejecutable. Por tanto, fabricar un MSI x86 sin resolver primero esa incompatibilidad produciría un paquete incompleto o engañoso. La build publicada permanece en Windows x64 hasta que todo el stack sea realmente compatible con x86.

## Linux desktop packaging

Linux no utiliza un framework GUI distinto. `src.desktop` se empaqueta con PyInstaller como en los otros sistemas. `scripts/build_desktop.py` crea un AppDir con `AppRun`, `.desktop` e icono SVG y `appimagetool` genera el AppImage x86_64.

Esto permite una aplicación Linux portable sin exigir una distribución concreta ni un instalador de paquetes del sistema.

## Release automation

`.github/workflows/release.yml` se activa al crear `vX.Y.Z` o manualmente para un tag existente.

El workflow:

1. hace checkout del tag exacto;
2. ejecuta `uv lock --check` y `uv sync --locked`;
3. construye Linux x86_64, Windows x64 y macOS en runners nativos;
4. valida los artefactos y la arquitectura Windows;
5. comprime el `.app` de macOS;
6. publica los artefactos como assets de workflow;
7. crea la GitHub Release si no existe o hace upload con `--clobber` si ya existe.

GitHub sigue generando automáticamente los ZIP/TAR de código fuente para el tag. La release final contiene, por tanto, tanto los fuentes automáticos como los binarios nativos sin intervención manual.

Artefactos esperados:

```text
VideoTranslationPipeline-X.Y.Z-linux-x86_64.AppImage
VideoTranslationPipeline-X.Y.Z-windows-x64.msi
VideoTranslationPipeline-X.Y.Z-windows-x64-portable.zip
VideoTranslationPipeline-X.Y.Z-macos.app.zip
```

El `.exe` correspondiente permanece dentro del paquete portable generado por PyInstaller.

## Versionado y lockfile

`pyproject.toml` es la fuente declarativa y `uv.lock` la resolución reproducible. Cada release debe sincronizar ambos.

El workflow de sincronización de releases comprueba que el historial de `CHANGELOG.md` no se reduzca ni se eliminen releases anteriores. Los títulos históricos se conservan y solo se modifican los contenidos cuando existe una corrección documental explícita.

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
uv run ruff check . --select S
uv run ruff format --check .
uv run python -m compileall .
uv build
```

Para validar desktop localmente en la plataforma correspondiente:

```bash
uv run python scripts/build_desktop.py --clean --version 1.10.0 --format native
uv run python scripts/build_desktop.py --clean --version 1.10.0 --format windows-msi --windows-arch x64
uv run python scripts/build_desktop.py --clean --version 1.10.0 --format linux-appimage
```

El build Windows requiere Windows y WiX; el build Linux requiere Linux y `appimagetool`. La firma/notarización de macOS y firma de editor de Windows son operaciones de publicación y requieren credenciales específicas.
