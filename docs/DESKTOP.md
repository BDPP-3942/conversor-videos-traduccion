# Aplicación de escritorio

La aplicación de escritorio de `1.9.0` es una capa de presentación sobre `VideoTranslationApplication` y el `MediaPipeline` existente. No duplica la lógica de STT, traducción, TTS, procesamiento multimedia ni almacenamiento.

## Instalación y ejecución

En un entorno de desarrollo:

```bash
uv sync --group dev
uv run video-translation-desktop
```

La GUI expone:

- almacenamiento local, Google Drive y rclone;
- idiomas, proveedor principal y proveedores de respaldo de traducción;
- paralelismo de vídeos y tamaño de lote de traducción;
- modelo, dispositivo, cálculo y beam de Whisper;
- WebM y TTS Kokoro;
- reanudación y normalización de nombres heredados;
- recuperación `full`, `stt_only` y `translate_only`;
- análisis y eliminación confirmada de duplicados;
- diagnóstico y preparación de Whisper;
- ejecución en segundo plano, progreso, registro y cancelación cooperativa;
- selección de un archivo de contexto para el prompt inicial de Whisper.

La autenticación de proveedores mantiene los flujos CLI existentes cuando requiere OAuth o configuración interactiva de rclone.

## Carpetas de trabajo y permisos

La aplicación no utiliza `Program Files` como área de datos de trabajo. La separación es intencionada:

```text
Windows:
C:\Program Files\VideoTranslationPipeline\
    → ejecutable y recursos de solo lectura

%USERPROFILE%\Documents\Video Translation Pipeline\
    ├── input\
    └── output\
        → medios y resultados gestionados por el usuario

%LOCALAPPDATA%\VideoTranslationPipeline\
    → estado, logs, cachés y datos internos
```

En macOS y Linux se utiliza el equivalente convencional de `Documentos` para `input`/`output` y el directorio de datos de aplicación del usuario para el estado interno.

Las carpetas de `Documentos` son solo el valor predeterminado. La GUI permite seleccionar cualquier otra carpeta con permisos de escritura, incluidas carpetas compartidas, unidades de red y carpetas sincronizadas por servicios como OneDrive o Dropbox.

No se conceden permisos de escritura especiales sobre `Program Files`. Esto evita depender de elevación de privilegios y mantiene la instalación separada de los datos del usuario.

## Control del pipeline

`ControllableMediaPipeline` adapta el pipeline existente para exponer eventos de preparación, descarga, extracción, conversión, transcripción, traducción, finalización, ZIP, error y cancelación.

La cancelación es cooperativa: se detiene en límites seguros y no termina a la fuerza una ejecución activa de FFmpeg o Whisper, evitando estados parciales o corruptos.

## Arquitectura

```text
Interfaz Tk/ttk
       |
       v
VideoTranslationApplication
       |
       v
ControllableMediaPipeline
       |
       v
MediaPipeline + adaptadores existentes
       |
       +-- STT / Whisper
       +-- proveedores de traducción + respaldo
       +-- Kokoro TTS
       +-- FFmpeg
       +-- almacenamiento local / Google Drive / rclone
       +-- resume / nombres / deduplicación
```

La fachada es independiente de Tk para permitir reutilizar los mismos casos de uso desde otras interfaces.

## Distribución nativa

La versión `1.9.0` distribuye aplicaciones de escritorio nativas para los tres sistemas objetivo:

| Plataforma | Construcción | Artefacto |
| --- | --- | --- |
| Windows x64 | PyInstaller + WiX 6 | `.exe` + `.msi` x64 |
| Windows x86 | PyInstaller x86 + WiX 6, solo si todo el conjunto de dependencias es compatible | `.exe` + `.msi` x86 |
| macOS | PyInstaller `BUNDLE` | `.app` dentro de `.zip` |
| Linux x86_64 | PyInstaller + AppDir + appimagetool | `.AppImage` |

Un ejecutable x64 no puede ejecutarse en Windows x86. Por ello, el proyecto no presenta el MSI x64 como compatible con sistemas de 32 bits. El soporte x86 requiere un build x86 real de Python, PyInstaller y todas las dependencias binarias necesarias.

### Windows

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format windows-msi
```

El ejecutable lo genera PyInstaller y el MSI lo genera WiX 6 a partir del bundle. El paquete x64 se instala en el `Program Files` nativo del sistema. El paquete x86, cuando exista, utiliza la ubicación de `Program Files` correspondiente a aplicaciones de 32 bits.

El instalador crea además un acceso directo en el menú Inicio para que Windows Search pueda localizar la aplicación.

### Linux

Linux utiliza el mismo ejecutable GUI generado por PyInstaller que el resto de plataformas. `scripts/build_desktop.py` crea un AppDir con:

- el bundle bajo `usr/bin/VideoTranslationPipeline`;
- `AppRun` como lanzador;
- `VideoTranslationPipeline.desktop` para la integración con el escritorio;
- `VideoTranslationPipeline.svg` como icono.

Finalmente `appimagetool` genera `VideoTranslationPipeline-<version>-linux-x86_64.AppImage`.

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format linux-appimage
```

### macOS

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format native
```

PyInstaller genera `VideoTranslationPipeline.app`. La firma y la notarización son operaciones de publicación que requieren credenciales de release y no forman parte de cada PR.

## Artefactos de GitHub Release

`.github/workflows/release.yml` se activa al publicar un tag `vX.Y.Z` y construye los artefactos en runners nativos.

La validación de escritorio debe comprobar al menos:

1. ejecutable GUI;
2. MSI de Windows correspondiente a la arquitectura construida;
3. AppImage de Linux;
4. `.app` de macOS;
5. ausencia de escritura requerida dentro de `Program Files`;
6. creación y utilización de las carpetas de usuario;
7. acceso directo del menú Inicio en Windows.

Los nombres de artefacto deben conservar la arquitectura cuando exista más de una variante, por ejemplo:

```text
VideoTranslationPipeline-1.9.0-windows-x64.msi
VideoTranslationPipeline-1.9.0-windows-x86.msi
VideoTranslationPipeline-1.9.0-linux-x86_64.AppImage
VideoTranslationPipeline-1.9.0-macos.app.zip
```

No debe publicarse un artefacto x86 si las dependencias del ejecutable no pueden construirse y probarse realmente para x86.

## CLI y ejecución programada

La GUI es una capa adicional. La CLI continúa siendo el contrato de automatización:

```bash
uv run video-translation-pipeline run
uv run video-translation-pipeline run --scheduled
```

También se conservan regeneración, QA de subtítulos, TTS, wrappers desatendidos y programación mediante launchd, cron y el Programador de tareas de Windows.

## Alcance de la release

La release `1.9.0` incorpora la aplicación de escritorio, el endurecimiento de extracción ZIP/Unicode y el empaquetado nativo. El soporte móvil permanece fuera del alcance del producto.

## Documentación relacionada

- [`README.md`](../README.md)
- [`CLI.md`](CLI.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`PACKAGING.md`](PACKAGING.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`RELEASES.md`](RELEASES.md)
