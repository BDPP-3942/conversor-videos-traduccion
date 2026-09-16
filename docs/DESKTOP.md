# Aplicación de escritorio

La aplicación de escritorio es una capa de presentación sobre `VideoTranslationApplication` y `MediaPipeline`. No duplica la lógica de STT, traducción, TTS, procesamiento multimedia ni almacenamiento.

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
- activación opcional de WebM y TTS;
- reanudación y normalización de nombres heredados;
- recuperación `full`, `stt_only` y `translate_only`;
- análisis y eliminación confirmada de duplicados;
- diagnóstico y preparación de Whisper;
- instalación del modelo local de traducción;
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

## WebM y TTS

WebM y TTS son capacidades opcionales y están desactivadas por defecto cuando la configuración no las activa. La GUI presenta controles de activación/desactivación independientes para que el usuario pueda aplicar los valores booleanos de configuración sin convertirlos en requisitos del procesamiento.

El TTS obligatorio es una propiedad distinta: `TTS_REQUIRED` solo debe activarse cuando se quiera que un fallo de TTS impida considerar completado el procesamiento. Activar TTS no implica exigirlo.

## Modelo local de traducción

La preparación del modelo local se realiza mediante el botón de instalación de la GUI, que delega en `LocalTranslationModelManager` y conserva la misma ruta de configuración y validación que la CLI. La instalación es una acción explícita y no se ejecuta automáticamente durante cada procesamiento.

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

La distribución se construye en la plataforma y arquitectura de destino. Cada artefacto debe corresponder a la arquitectura real del intérprete Python y de sus dependencias binarias.

| Plataforma | Construcción | Artefacto |
| --- | --- | --- |
| Windows x64 | PyInstaller + WiX 6 | `.exe` + `.msi` x64 |
| Windows x86 | PyInstaller x86 + WiX 6, cuando el conjunto de dependencias sea compatible | `.exe` + `.msi` x86 |
| macOS | PyInstaller `BUNDLE` | `.app` dentro de `.zip` |
| Linux x86_64 | PyInstaller + AppDir + appimagetool | `.AppImage` |

Un ejecutable x64 no puede ejecutarse en Windows x86. Por ello, un MSI x64 no debe anunciar compatibilidad con sistemas de 32 bits. Una variante x86 requiere un build x86 real de Python, PyInstaller y todas las dependencias binarias necesarias; no basta con cambiar el nombre del artefacto.

### Windows

El comando general es:

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format windows-msi --windows-arch <x64|x86>
```

`--windows-arch` debe coincidir con la arquitectura del intérprete Python que ejecuta PyInstaller. WiX recibe la misma arquitectura para generar el MSI correspondiente.

El ejecutable x64 se instala en el `Program Files` nativo del sistema. Una build x86 real utiliza la ubicación de `Program Files` correspondiente a aplicaciones de 32 bits.

El instalador crea además un acceso directo en el menú Inicio para que Windows Search pueda localizar la aplicación.

### Linux

Linux utiliza el mismo ejecutable GUI generado por PyInstaller que el resto de plataformas. `scripts/build_desktop.py` crea un AppDir con:

- el bundle bajo `usr/bin/VideoTranslationPipeline`;
- `AppRun` como lanzador;
- `VideoTranslationPipeline.desktop` para la integración con el escritorio;
- `VideoTranslationPipeline.svg` como icono.

Finalmente `appimagetool` genera el AppImage x86_64.

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format linux-appimage
```

### macOS

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format native
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
VideoTranslationPipeline-<version>-windows-x64.msi
VideoTranslationPipeline-<version>-windows-x86.msi
VideoTranslationPipeline-<version>-linux-x86_64.AppImage
VideoTranslationPipeline-<version>-macos.app.zip
```

No debe publicarse un artefacto x86 si las dependencias del ejecutable no pueden construirse y probarse realmente para x86.

## CLI y ejecución programada

La GUI es una capa adicional. La CLI continúa siendo el contrato de automatización:

```bash
uv run video-translation-pipeline run
uv run video-translation-pipeline run --scheduled
```

También se conservan regeneración, QA de subtítulos, TTS, wrappers desatendidos y programación mediante launchd, cron y el Programador de tareas de Windows.

## Documentación relacionada

- [`README.md`](../README.md)
- [`CLI.md`](CLI.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`PACKAGING.md`](PACKAGING.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`RELEASES.md`](RELEASES.md)
