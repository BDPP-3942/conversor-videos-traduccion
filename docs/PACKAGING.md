# Empaquetado

El proyecto utiliza PyInstaller para generar aplicaciones de escritorio y WiX 6 para el instalador MSI de Windows. La construcción se realiza en el sistema operativo y arquitectura de destino; no se utilizan builds cruzados para producir ejecutables nativos.

## Dependencias de construcción

Las herramientas de build están declaradas en el grupo de dependencias de desarrollo de uv. Para incluir el runtime opcional de TTS durante la construcción:

```bash
uv sync --group dev --extra tts
```

No existe un extra `[package]` independiente en `pyproject.toml`; las herramientas de empaquetado pertenecen al grupo `dev`.

## Aplicación de escritorio

El punto de entrada es:

```bash
uv run video-translation-desktop
```

La aplicación utiliza la lógica común de `VideoTranslationApplication` y `MediaPipeline`; el empaquetado no crea un segundo motor de procesamiento.

## Windows

Construcción del MSI:

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format windows-msi
```

La arquitectura se obtiene del intérprete Python utilizado para construir PyInstaller. También puede solicitarse explícitamente:

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format windows-msi --windows-arch x64
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format windows-msi --windows-arch x86
```

La segunda variante solo es válida si el entorno Python x86 y todas las dependencias binarias del proyecto pueden construirse realmente para x86.

El script pasa la arquitectura a WiX mediante la opción `-arch`; no depende de una variable de preprocesador `Platform` inventada. El archivo WiX utiliza `ProgramFilesFolder`, y WiX genera el MSI con la arquitectura solicitada. Por tanto:

- MSI x64 → `Program Files` nativo del sistema.
- MSI x86 → ubicación de `Program Files` correspondiente a aplicaciones de 32 bits en sistemas x64.

La aplicación no escribe datos de trabajo dentro de la instalación.

## Linux

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format linux-appimage
```

PyInstaller genera el bundle y `appimagetool` lo encapsula como AppImage.

## macOS

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format native
```

PyInstaller genera `VideoTranslationPipeline.app`. La firma y notarización pertenecen al proceso de publicación y requieren credenciales de release.

## Datos de runtime

El instalador contiene el software, pero no debe utilizar la carpeta de instalación como almacén escribible. La aplicación separa:

```text
Instalación
└── ejecutable + recursos de solo lectura

Documentos/Video Translation Pipeline/
├── input/
└── output/

Datos privados de la aplicación
└── estado, logs, cachés, trabajo temporal y manifests internos
```

La GUI permite cambiar `input` y `output` por cualquier carpeta donde el usuario tenga permisos de escritura.

## Validación

La validación mínima antes de una release es:

```bash
uv lock --check
uv run ruff check . --select F401,I001
uv run ruff check .
uv run ruff check . --select S
uv run ruff format --check .
uv run python -m compileall .
uv run pytest -q --ignore=tests/test_packaging.py
uv build
```

Además, CI construye el artefacto nativo de cada plataforma en su runner correspondiente y comprueba que el archivo esperado exista.

## Documentación relacionada

- [`DESKTOP.md`](DESKTOP.md): uso de la aplicación de escritorio.
- [`CLI.md`](CLI.md): comandos y opciones de la CLI.
- [`INSTALLATION.md`](INSTALLATION.md): instalación del proyecto.
- [`CI_CD.md`](CI_CD.md): validación continua y publicación.
- [`RELEASES.md`](RELEASES.md): alcance de las releases.
