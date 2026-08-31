# Project overview

## Purpose

**Video Translation Pipeline** is a batch-oriented Python application for audiovisual localization. It accepts video files or ZIP packages, normalizes media, transcribes speech, creates and validates WebVTT subtitles, translates subtitle cues while preserving their timing, and can optionally synthesize synchronized narration with Kokoro TTS.

It is designed for unattended operation and supports local storage, Google Drive and rclone-backed storage.

## Scope

Implemented capabilities include:

- video/ZIP ingestion;
- FFmpeg-based media processing;
- STT with `faster-whisper`;
- silence-aware cue segmentation and VTT validation;
- configurable translation providers with fallback and retry controls;
- local, Google Drive and rclone storage adapters;
- manifests, resume/idempotent processing and artifact validation;
- conservative duplicate-output management;
- optional synchronized Kokoro TTS;
- resource-aware video concurrency based on detected CPU, RAM and optional GPU capacity;
- CLI entry points and unattended execution;
- Windows/Linux/macOS scheduler helpers; portable packaging scripts are currently provided for Windows and Linux;
- automated tests, linting, security checks, packaging and dependency audits.

The application is not an interactive video editor and automated translation/TTS output still requires human quality review when accuracy matters.

## Runtime contract

The canonical runtime entry point is `main.py`. Installed packages also expose `video-translation-pipeline`, `video-subtitle-qa` and `video-translation-tts` entry points.

The default configuration uses local storage:

```text
local://storage/input → pipeline → local://storage/output
```

See [INSTALLATION.md](INSTALLATION.md), [CONFIGURATION.md](CONFIGURATION.md) and [CLI.md](CLI.md) for operational details.

## Current main vs published release

The latest published release is `1.2.2`, and `pyproject.toml` on `main` is aligned to `1.2.2`. The current `main` branch also contains changes merged after that release. These post-release changes are documented separately and must not be retroactively attributed to `1.2.2`.

The most relevant post-release functional change is PR #20: resource-aware video concurrency. It makes `max_parallel_videos = 0` mean AUTO and calculates a conservative concurrency ceiling from the resolved Whisper configuration and available CPU, RAM and GPU resources. Positive values remain upper bounds and may be clamped. This behavior is part of current `main`, not the published `1.2.2` release.

PR #21 only aligns the package metadata with the already published `1.2.2` release; it does not introduce a product capability.

See [RELEASES.md](RELEASES.md) for the release history and the distinction between published releases and subsequent changes on `main`.

## Verified release evidence

| Capability | First verified product release | Evidence |
|---|---:|---|
| Core audiovisual pipeline, STT, VTT, translation, storage, resume/idempotency, conservative deduplication, TTS, scheduling and packaging | `1.0.0` | `CHANGELOG.md` / release history |
| VTT recovery/repair and integrated synchronized TTS | `1.1.0` | `CHANGELOG.md` / release history |
| Naming improvements and TTS asset bootstrap | `1.2.0` | `CHANGELOG.md` / release history |
| TTS installation fix | `1.2.1` | release history |
| Timestamp cleanup in naming | `1.2.2` | release history |
| Resource-aware video concurrency | **Post-`1.2.2`** | PR #20; not yet assigned to a published release |

The table records only functionality for which the repository provides evidence. Post-release changes are not assigned a release version until a corresponding release exists.
