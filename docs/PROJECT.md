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

## Current candidate vs published release

The latest published release remains `1.5.1`. The current branch prepares the compatible PATCH candidate `1.6.1`, which fixes the `faster-whisper` selective STT recovery regression introduced in the `1.6.0` feature line.

Release `1.6.0` introduced optional local translation, GPU/runtime hardening and configurable selective STT recovery. Release `1.6.1` corrects the recovery backend contract without changing the public recovery configuration or the audiovisual pipeline.

See [RELEASES.md](RELEASES.md) for the release history and [../RELEASE_CANDIDATE.md](../RELEASE_CANDIDATE.md) for the exact release-gate scope.

## Verified release evidence

| Capability | First verified product release | Evidence |
|---|---:|---|
| Core audiovisual pipeline, STT, VTT, translation, storage, resume/idempotency, conservative deduplication, TTS, scheduling and packaging | `1.0.0` | `CHANGELOG.md` / release history |
| VTT recovery/repair and integrated synchronized TTS | `1.1.0` | `CHANGELOG.md` / release history |
| Naming improvements and TTS asset bootstrap | `1.2.0` | `CHANGELOG.md` / release history |
| TTS installation fix | `1.2.1` | release history |
| Timestamp cleanup in naming | `1.2.2` | release history |
| Resource-aware video concurrency | `1.3.0` | release history |
| Clean regeneration | `1.4.0` | release history |
| Multiplatform Whisper/context and packaging | `1.5.0` | release history |
| ZIP/filesystem hardening | `1.5.1` | release history |
| Local translation, GPU/runtime hardening and configurable STT recovery | `1.6.0` | release history |
| `faster-whisper` selective recovery `clip_timestamps` compatibility fix | `1.6.1` | `CHANGELOG.md` / `RELEASES.md` |

The table records only functionality for which the repository provides release evidence. `1.6.1` remains a candidate until its final SHA passes the release gate and the tag is created after merge.
