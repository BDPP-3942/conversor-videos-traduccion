# Desktop application

La aplicación de escritorio de `1.9.0` es una capa de presentación sobre la fachada de aplicación y el `MediaPipeline` existente. No duplica STT, traducción, TTS, media ni almacenamiento.

## Install and run

```bash
uv sync --group dev
uv run video-translation-desktop
```

La GUI expone:

- almacenamiento local, Google Drive y rclone;
- idiomas, proveedor principal y fallbacks de traducción;
- paralelismo de vídeos y batching de traducción;
- modelo/device/compute/beam de Whisper;
- WebM y TTS Kokoro;
- resume y normalización de nombres heredados;
- recuperación `full`, `stt_only` y `translate_only`;
- scan, análisis, dry-run y eliminación confirmada de duplicados;
- diagnósticos y preparación de Whisper;
- ejecución en background, eventos de etapa, porcentaje, fichero actual, log y cancelación segura.

La autenticación de proveedores continúa utilizando los flujos CLI/setup existentes cuando requiere OAuth o configuración interactiva de rclone.

## Pipeline control

`ControllableMediaPipeline` adapta el pipeline existente para exponer eventos de preparación, descarga, extracción, conversión, transcripción, traducción, finalización, ZIP, error y cancelación.

La cancelación es cooperativa: se detiene en límites seguros y no mata a la fuerza una ejecución activa de FFmpeg/Whisper, evitando estados parciales o corruptos.

## Architecture

```text
Tk/ttk Desktop UI
        |
        v
VideoTranslationApplication
        |
        v
ControllableMediaPipeline
        |
        v
Existing MediaPipeline + adapters
        |
        +-- STT / Whisper
        +-- translation providers + fallback
        +-- Kokoro TTS
        +-- FFmpeg
        +-- local / Google Drive / rclone storage
        +-- resume / naming / deduplication
```

La fachada es independiente de Tk para permitir reutilizar los casos de uso desde otra interfaz.

## Native distribution

La versión `1.9.0` distribuye una aplicación GUI nativa en los tres sistemas objetivo:

| Plataforma | Construcción | Artefacto de release |
|---|---|---|
| Windows x64 | PyInstaller + WiX 6.0.2 | `.exe` + `.msi` |
| macOS | PyInstaller `BUNDLE` | `.app` dentro de un `.zip` |
| Linux x86_64 | PyInstaller + AppDir + appimagetool | `.AppImage` |

### Linux: método utilizado

Linux usa el mismo ejecutable GUI que Windows/macOS en cuanto a tecnología de aplicación: **PyInstaller empaqueta `src.desktop` y sus dependencias en un bundle ejecutable**. Después `scripts/build_desktop.py` crea un AppDir con:

- el bundle PyInstaller bajo `usr/bin/VideoTranslationPipeline`;
- `AppRun` como launcher;
- `VideoTranslationPipeline.desktop` para integración con el escritorio;
- `VideoTranslationPipeline.svg` como icono.

Finalmente `appimagetool` convierte ese AppDir en `VideoTranslationPipeline-<version>-linux-x86_64.AppImage`. AppImage es la capa de distribución portable; no es un segundo framework GUI.

Build local:

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format linux-appimage
```

### Windows

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format windows-msi
```

El `.exe` lo genera PyInstaller y el `.msi` lo genera WiX 6.0.2 a partir del bundle.

### macOS

```bash
uv run python scripts/build_desktop.py --clean --version 1.9.0 --format native
```

PyInstaller genera `VideoTranslationPipeline.app`. La firma y notarización son operaciones de publicación que requieren credenciales de release y no se realizan en cada PR.

## Automated GitHub Release artifacts

No es necesario compilar ni subir manualmente los binarios en cada release.

`.github/workflows/release.yml` se activa automáticamente cuando se publica un tag `vX.Y.Z` y:

1. comprueba el `uv.lock` del tag;
2. crea el entorno bloqueado;
3. construye en runners nativos Ubuntu, Windows y macOS;
4. valida el AppImage, MSI, EXE y `.app`;
5. comprime el `.app` de macOS;
6. descarga los tres artefactos en un job de publicación;
7. crea la GitHub Release si no existe o actualiza sus assets si ya existe.

Los nombres de release son deterministas:

```text
VideoTranslationPipeline-1.9.0-linux-x86_64.AppImage
VideoTranslationPipeline-1.9.0-windows-x64.msi
VideoTranslationPipeline-1.9.0-macos.app.zip
```

GitHub genera además automáticamente los ZIP/TAR del **código fuente** asociados al tag. Por tanto, una release de escritorio queda compuesta por los archivos fuente de GitHub más los tres artefactos nativos producidos por CI, sin intervención manual.

La firma/notarización de macOS y la firma de editor de Windows pueden añadirse posteriormente al mismo job mediante secretos de release sin cambiar el modelo de automatización.

## CLI and scheduled execution

La GUI es aditiva. Se mantienen:

```bash
uv run video-translation-pipeline run
uv run video-translation-pipeline run --scheduled
```

También se conservan regeneración, subtitle-QA, TTS, wrappers unattended y scheduling mediante launchd, cron y Task Scheduler.

Los modelos, credenciales y estado mutable siguen siendo recursos externos y no se embeben en el ejecutable.

## Release scope

Desktop es `1.9.0` y no soporte móvil. El móvil permanece fuera del alcance del producto hasta una decisión futura explícita.
