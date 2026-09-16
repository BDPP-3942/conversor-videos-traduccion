# Empaquetado

El proyecto utiliza PyInstaller para generar aplicaciones de escritorio y WiX 6 para el instalador MSI de Windows. La construcción se realiza en el sistema operativo y arquitectura de destino; no se utilizan builds cruzados para producir ejecutables nativos.

## Dependencias de construcción

Las herramientas de build están declaradas en el grupo de dependencias de desarrollo de uv. Para incluir el runtime opcional de TTS durante la construcción:

```bash
uv sync --group dev --extra tts
```

Este comando sincroniza el entorno de desarrollo y activa el extra opcional `tts`, necesario cuando el ejecutable debe incluir el runtime de Kokoro. Las herramientas de empaquetado pertenecen al grupo `dev`.

## Aplicación de escritorio

El punto de entrada es:

```bash
uv run video-translation-desktop
```

`uv run` ejecuta el entry point dentro del entorno bloqueado del proyecto; `video-translation-desktop` inicia la GUI sin crear un segundo motor de procesamiento. La lógica continúa pasando por `VideoTranslationApplication` y `MediaPipeline`.

## Windows

Construcción del MSI:

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format windows-msi
```

`--clean` elimina restos de `build` y `dist`, `--version` fija la versión incluida en el nombre del artefacto y `--format windows-msi` solicita el ejecutable PyInstaller y el MSI WiX.

La arquitectura se obtiene del intérprete Python utilizado para construir PyInstaller. También puede solicitarse explícitamente:

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format windows-msi --windows-arch x64
uv run python scripts/build_desktop.py --clean --version <version> --format windows-msi --windows-arch x86
```

`--windows-arch` se transmite a WiX mediante `-arch`. La variante x86 solo es válida si el intérprete Python, PyInstaller y todas las dependencias binarias pueden construirse realmente para x86. El proyecto no debe declarar una build x86 como disponible mientras esa comprobación de compatibilidad no sea satisfactoria.

El MSI x64 se instala en el `Program Files` nativo. No se presenta un ejecutable x64 como compatible con Windows x86. El instalador no debe utilizar su directorio de instalación como espacio de trabajo escribible.

## Linux

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format linux-appimage
```

El comando genera el ejecutable PyInstaller, crea el AppDir con `AppRun`, metadata `.desktop` e icono SVG y ejecuta `appimagetool` para producir el AppImage x86_64. CI ejecuta esta operación en un runner Linux nativo.

## macOS

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format native
```

El comando genera `VideoTranslationPipeline.app`. En la publicación se archiva como ZIP; la firma y notarización pertenecen al proceso de release y requieren las credenciales correspondientes.

## Builds de release

La workflow de release utiliza la versión del tag `vX.Y.Z` para nombrar y validar los artefactos. Los comandos de esta guía utilizan `<version>` para no acoplar la documentación técnica a una release concreta.

La publicación definitiva se realiza mediante [`.github/workflows/release.yml`](../.github/workflows/release.yml) al crear un tag `vX.Y.Z`. No se deben publicar binarios generados manualmente desde un equipo de desarrollo.

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

La GUI permite cambiar `input` y `output` por cualquier carpeta donde el usuario tenga permisos de escritura, incluida una carpeta compartida, de red o sincronizada.

## Validación

La validación mínima antes de integrar cambios es:

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

`uv lock --check` verifica que el lockfile corresponde al proyecto; `ruff check` valida lint, imports y reglas de calidad; `ruff format --check` comprueba el formato sin modificar archivos; `compileall` comprueba que Python pueda compilar el código; `pytest` ejecuta la suite y `uv build` valida la construcción de distribución Python.

Además, CI construye el artefacto nativo de cada plataforma en su runner correspondiente y comprueba que el archivo esperado exista.

## Documentación relacionada

- [`DESKTOP.md`](DESKTOP.md): uso de la aplicación de escritorio.
- [`CLI.md`](CLI.md): comandos y opciones de la CLI.
- [`INSTALLATION.md`](INSTALLATION.md): instalación del proyecto.
- [`CI_CD.md`](CI_CD.md): validación continua y publicación.
- [`RELEASES.md`](RELEASES.md): histórico y alcance de las releases.
