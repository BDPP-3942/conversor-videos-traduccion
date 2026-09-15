# Release Candidate — 1.9.0

## Release

- **Version:** `1.9.0`
- **Classification:** MINOR
- **Previous published baseline:** `v1.8.2`
- **Target tag:** `v1.9.0`
- **Status:** unreleased; pending final CI, Release Gate and merge to `main`.

## Scope

`1.9.0` introduces the desktop GUI and native distribution layer described in `docs/DESKTOP.md` and `RELEASE_SCOPE.md`.

### Product changes

- New `video-translation-desktop` entry point.
- GUI tabs for processing, subtitle recovery, duplicate management, diagnostics and CLI/scheduling guidance.
- Reuse of the existing `MediaPipeline` through `VideoTranslationApplication` and `ControllableMediaPipeline`.
- Stage-based progress events and cooperative safe-boundary cancellation.
- Configuration of storage providers, languages, translation providers/fallbacks, concurrency, Whisper, WebM, TTS, resume and naming behavior from the GUI.
- Recovery modes `full`, `stt_only` and `translate_only`.
- Duplicate scan/analyze/delete workflows with dry-run and confirmation.

### Packaging changes

- PyInstaller desktop bundle.
- Windows `.exe` and WiX 6 `.msi`.
- macOS `.app`.
- Linux x86_64 AppImage built from a PyInstaller executable plus AppDir metadata.
- Native packaging validation on Linux, Windows and macOS.

### Release engineering

- Tag-driven GitHub Release workflow automatically builds native artifacts on native runners and attaches them to the GitHub Release.
- Source-code archives remain GitHub's automatic tag archives.
- No manual build/upload step is required for normal releases.
- `uv.lock` is required to match the `1.9.0` project metadata.

## Compatibility

- Existing CLI entry points remain supported.
- Scheduled/headless execution remains supported.
- Existing regeneration, subtitle-QA and TTS commands remain supported.
- No mobile application is included.
- Desktop is an additive presentation/distribution layer and does not replace the existing processing pipeline.

## Validation required before publication

- Linux, Windows and macOS.
- Python 3.11, 3.12 and 3.13.
- Full pytest suite.
- Ruff lint, import sorting and formatting.
- `uv lock --check` and `uv sync --locked`.
- `uv pip check` and packaging validation.
- Native desktop builds and artifact smoke validation on all target operating systems.
- Release Gate on the exact final `main` SHA.

## Publication rule

Create `v1.9.0` only from the exact final SHA that has passed the complete release validation on `main`. Once the tag is pushed, `.github/workflows/release.yml` builds and attaches the desktop artifacts automatically.
