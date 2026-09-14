# Desktop application

`main` remains the functional source of truth. The desktop application is a presentation layer over the existing application/use-case facade and `MediaPipeline`; it does not duplicate STT, translation, TTS, media or storage implementations.

## Install and run

```bash
uv sync --group dev
uv run video-translation-desktop
```

The GUI exposes the principal processing and maintenance workflows:

- local input/output folder selection and saved cloud-provider selection;
- source/target languages and primary/fallback translation providers;
- automatic or bounded video parallelism and translation batching;
- Whisper model/device/compute/beam settings;
- WebM generation and synchronized Kokoro TTS options;
- resume and legacy-name normalization controls;
- optional automatic local output deduplication;
- subtitle recovery for one output or all eligible outputs (`full`, STT-only, translation-only);
- duplicate scan, analysis, dry-run deletion and confirmed deletion;
- runtime doctor and Whisper prefetch;
- background execution so the GUI remains responsive;
- stage events, percentage progress, current file, completion and safe cancellation requests;
- retained technical execution log and user-facing errors.

Provider authentication/profile creation remains available through the existing CLI because it can require browser OAuth or interactive rclone configuration. The GUI does not remove or bypass those contracts.

## Pipeline control

`ControllableMediaPipeline` wraps the existing pipeline without replacing its processing logic. It exposes explicit lifecycle events such as preparation, download, extraction, conversion, transcription, translation, finalization, ZIP completion, error and cancellation. Cancellation is cooperative: the application requests cancellation and the pipeline stops at a safe stage boundary instead of force-killing FFmpeg/Whisper work or risking partial artifacts.

The underlying heavy operations remain synchronous within their existing workers, so a cancellation request is not guaranteed to interrupt an already-running FFmpeg or Whisper invocation immediately. This is intentional and documented rather than presenting unsafe process termination as a feature.

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

The application facade is deliberately independent of Tk so another UI or service can reuse the same use cases.

## Distribution

Build on the target operating system with the same Python/runtime environment used by CI:

```bash
uv sync --group dev
uv run python scripts/build_desktop.py --clean --version 1.8.3 --format native
```

The resulting native formats are:

| Platform | Primary artifact | Installer/distribution |
|---|---|---|
| Windows x64 | `VideoTranslationPipeline.exe` | `.msi` generated with WiX v4 |
| macOS | `VideoTranslationPipeline.app` | `.app` bundle; signing/notarization is a release-stage operation |
| Linux x86_64 | PyInstaller executable bundle | `.AppImage`; a `.tar.gz` portable bundle can also be distributed |

Windows MSI:

```text
uv run python scripts/build_desktop.py --clean --version 1.8.3 --format windows-msi
```

Linux AppImage:

```text
uv run python scripts/build_desktop.py --clean --version 1.8.3 --format linux-appimage
```

The repository CI validates the native packaging workflow on Windows, macOS and Linux. Release publication must additionally validate the installed artifact on each target OS. macOS signing/notarization and Windows publisher signing require release credentials and are not performed by ordinary pull-request CI.

Models, credentials and mutable runtime state remain external resources; they are not embedded into the desktop executable.

## CLI and scheduled execution

The desktop application is additive. The existing CLI remains supported:

```bash
uv run video-translation-pipeline run
uv run video-translation-pipeline run --scheduled
```

The scheduled/headless paths remain independent of a graphical session. Existing scheduling integrations continue to be supported, including macOS `launchd`, cron-style Linux/macOS execution, and Windows Task Scheduler through the existing unattended wrappers. See `docs/CLI.md` and `docs/SCHEDULING.md` for the operational contracts.

The desktop entry point is an additional executable interface; it does not replace the existing CLI entry points, unattended wrappers or scheduled tasks.
