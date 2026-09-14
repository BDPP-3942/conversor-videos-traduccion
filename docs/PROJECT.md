# Project overview

## Purpose

**Video Translation Pipeline** is a batch-oriented Python application for audiovisual localization. It accepts video files or ZIP packages, normalizes media, transcribes speech, creates and validates WebVTT subtitles, translates subtitle cues while preserving their timing, and can optionally synthesize synchronized narration with Kokoro TTS.

It is designed for unattended operation and supports local storage, Google Drive and rclone-backed storage.

## Scope

Implemented capabilities include video/ZIP ingestion, FFmpeg processing, STT with `faster-whisper`, VTT validation, configurable translation providers, local/Google Drive/rclone storage, manifests/resume/idempotency, duplicate-output management, optional TTS, resource-aware concurrency, CLI entry points, unattended execution, multiplatform scheduler helpers, portable packaging, tests, linting, security checks and dependency audits.

## Runtime contract

The canonical runtime entry point is `main.py`. Installed packages also expose `video-translation-pipeline`, `video-subtitle-qa` and `video-translation-tts` entry points.

The default configuration uses local storage:

```text
local://storage/input → pipeline → local://storage/output
```

## Current release candidate

The current candidate is `1.8.3`. It is a PATCH release that fixes the mismatch between the project-managed uv bootstrap and wrappers that previously required a global `uv` on `PATH`.

The documented setup may install `uv` under `tools/uv/` without changing shell profiles. All affected source-checkout wrappers now resolve that managed executable first, then fall back to `PATH`.

Affected entry points are `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*`, `build_linux.sh` and `build_windows.bat`. The packaged executable remains the first choice for unattended execution, and the direct `.venv` Python fallback is retained when uv cannot be resolved.

Regression coverage is provided by `tests/test_uv_resolution_contract.py` for POSIX and Windows wrapper contracts.

See [INSTALLATION.md](INSTALLATION.md), [UV_MIGRATION.md](UV_MIGRATION.md), [RELEASES.md](RELEASES.md) and [../RELEASE_CANDIDATE.md](../RELEASE_CANDIDATE.md).

## Release history

- `v1.8.0` — current previously published product release and immutable baseline.
- `1.8.2` — unreleased candidate state superseded by `1.8.3`.
- `1.8.3` — current candidate for the project-managed uv wrapper regression.
- Earlier releases from `1.0.0` through `1.7.4` remain historical and immutable.

The runtime version is sourced from `pyproject.toml` and `config/app.toml`, not from this document.
