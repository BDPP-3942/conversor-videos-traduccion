# Desktop application

`main` remains the functional source of truth. The desktop application adds a standard-library Tk/ttk presentation layer over an application/use-case facade and the existing `MediaPipeline`; it does not duplicate STT, translation, TTS, media or storage logic.

## Install and run

```bash
uv sync --group dev
uv run video-translation-desktop
```

The GUI currently exposes the primary end-user processing workflow:

- local input/output folder selection;
- storage provider selection;
- source and target languages;
- translation provider selection;
- resource-aware video parallelism, including AUTO;
- optional WebM generation;
- optional synchronized TTS;
- background execution so the GUI thread remains responsive;
- readable progress/status messages and retained technical output.

Cloud provider setup, subtitle-only recovery, duplicate management and provider authentication remain available through the existing CLI until dedicated GUI views are added. They are not removed from the product contract.

## Architecture

```text
Tk/ttk Desktop UI
        |
        v
VideoTranslationApplication
        |
        v
MediaPipeline + existing adapters
        |
        +-- STT
        +-- translation providers
        +-- TTS
        +-- FFmpeg
        +-- storage
```

The application facade is deliberately independent of Tk so it can be reused by another UI or a future API service.

## Packaging

Build on the target operating system:

```bash
uv sync --group dev
uv run python scripts/build_desktop.py --clean
```

PyInstaller produces a portable directory under `dist/VideoTranslationPipeline/`. Models, credentials and runtime state remain external resources; they are not embedded into the executable.

The repository currently has CI coverage for Python package builds, not yet a verified end-to-end installed desktop binary on every operating system. A platform-specific executable must therefore not be described as release-ready solely because PyInstaller completes.

## Deliberate limitations

- Cooperative cancellation is not yet propagated through every long-running core stage. The GUI does not terminate FFmpeg/Whisper processes forcibly because doing so could leave incomplete artifacts.
- The current GUI is the first production-oriented desktop surface, not yet a complete visual replacement for every administrative CLI command.
- macOS code signing/notarization and platform-native installers require platform credentials/runners and are not claimed until built and executed on the target platform.
