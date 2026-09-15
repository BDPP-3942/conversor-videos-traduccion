# Release Scope — 1.9.0

## Release classification

`1.9.0` is the next **MINOR** release. It adds a backward-compatible desktop application and native distribution layer while preserving the existing CLI, scheduled execution and unattended wrappers.

The previous published baseline is `v1.8.2`. The historical `1.8.x` documentation remains immutable; the earlier `1.8.3` uv-resolution work is retained as historical candidate context and is not reclassified as the desktop release.

## Desktop application

The release adds a native GUI entry point, `video-translation-desktop`, implemented as a presentation layer over the existing pipeline rather than a second processing engine.

The GUI provides:

- processing from local storage, Google Drive and rclone-backed sources;
- source/target language and translation-provider selection;
- fallback providers, translation batch size and parallel-video controls;
- Whisper model/device/compute/beam configuration;
- WebM and TTS controls, including required-TTS behavior and voice/speed;
- resume and legacy-name normalization controls;
- subtitle recovery with `full`, `stt_only` and `translate_only` modes;
- duplicate scanning, analysis, dry-run and confirmed deletion;
- diagnostics for the environment and Whisper assets;
- live stage/progress events, background execution and cooperative cancellation;
- explicit retention of CLI and scheduled/headless execution.

Provider authentication/profile creation remains available through the established CLI/setup flows where OAuth or rclone configuration requires interactive credentials.

## Pipeline control architecture

`src/controllable_pipeline.py` adapts the existing `MediaPipeline` with stage events and cooperative cancellation. It does not duplicate audiovisual processing logic.

Cancellation is deliberately safe-boundary based: an active FFmpeg/Whisper native process is allowed to finish its current operation before the pipeline stops. This avoids corrupting intermediate artifacts while still giving the GUI a deterministic cancellation contract.

## Native packaging

The release produces platform-native desktop artifacts through PyInstaller and platform-specific packaging:

- **Windows:** PyInstaller GUI executable plus WiX 6 MSI installer.
- **macOS:** PyInstaller `.app` bundle, distributed as a release `.zip` for easy download.
- **Linux:** PyInstaller executable wrapped in an AppDir (`AppRun`, `.desktop` metadata and SVG icon) and packaged as an x86_64 AppImage with `appimagetool`.

Linux therefore uses the same GUI executable strategy as Windows/macOS; the distribution format is different because Linux does not have one universal native installer format. AppImage is used to provide a self-contained, portable GUI application.

## Release automation

A tag `vX.Y.Z` automatically starts `.github/workflows/release.yml`. The workflow:

1. checks out the exact tag;
2. validates `uv.lock` and installs the locked development environment;
3. builds Linux, Windows and macOS desktop artifacts on their native GitHub-hosted runners;
4. validates the expected executable/package on each platform;
5. archives the macOS `.app` as a `.zip`;
6. uploads all artifacts to the workflow;
7. creates the GitHub Release if necessary and attaches the binaries automatically.

GitHub continues to provide the source-code archives for the tag. The native desktop artifacts are attached alongside those source archives, so releases no longer require manual local builds or manual binary uploads.

The release workflow can also be dispatched for an existing tag to rebuild and replace its desktop assets.

## Version and lockfile consistency

For `1.9.0`, the version must be synchronized in:

- `pyproject.toml`;
- `config/app.toml`;
- `uv.lock`;
- `CHANGELOG.md`;
- `docs/RELEASES.md`;
- `docs/VERSIONING.md`;
- `RELEASE_CANDIDATE.md`;
- this file;
- related desktop/release documentation.

The project includes a temporary branch lock-refresh workflow while this release is being prepared so that changes to `pyproject.toml` cannot leave `uv.lock` stale. Normal development must still treat `uv.lock` as committed release metadata and require `uv lock --check`.

## CI and release gate

The existing Linux/Windows/macOS Python 3.11–3.13 matrix remains required. Desktop packaging adds native validation on all three operating systems. The final release SHA must pass tests, lint/format, compile checks, lockfile validation, packaging and Release Gate before its tag is considered publishable.

Mobile is explicitly outside the `1.9.0` scope.
