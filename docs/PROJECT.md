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

## Current published release vs candidate

The latest published product release is `1.7.0` (`v1.7.0`). This branch prepares the PATCH release `1.7.1` directly from the published `1.7.0` baseline.

Release `1.7.0` consolidated reprocessing/manifests, local-storage race hardening, deterministic Unicode naming/filesystem behavior and the local translation runtime. Release `1.7.1` corrects the `faster-whisper` selective-recovery backend contract without changing the public recovery configuration or the audiovisual pipeline.

The previous releases `1.6.0` and `1.5.1` remain historical context only. The compatibility review for `1.7.1` must compare against **`v1.7.0`**, so that none of the functionality already present in the latest project release is accidentally omitted from the assessment.

See [RELEASES.md](RELEASES.md) for the release history and [../RELEASE_CANDIDATE.md](../RELEASE_CANDIDATE.md) for the exact release-gate scope.

## Verified release evidence

| Capability | First verified product release | Evidence |
|---|---:|---|
| Core audiovisual pipeline, STT, VTT, translation, storage, resume/idempotency, conservative deduplication, TTS, scheduling and packaging | `1.0.0` | `CHANGELOG.md` / release history |
| VTT recovery/repair and integrated synchronized TTS | `1.1.0` | `CHANGELOG.md` / release history |
| Naming improvements and TTS asset bootstrap | `1.2.0` | release history |
| TTS installation fix | `1.2.1` | release history |
| Timestamp cleanup in naming | `1.2.2` | release history |
| Resource-aware video concurrency | `1.3.0` | release history |
| Clean regeneration | `1.4.0` | release history |
| Multiplatform Whisper/context and packaging | `1.5.0` | release history |
| ZIP/filesystem hardening | `1.5.1` | release history |
| Local translation, GPU/runtime hardening and configurable STT recovery | `1.6.0` | release history |
| Reprocessing/manifests, Unicode naming/filesystem consolidation and translation runtime improvements | `1.7.0` | published GitHub release |
| `faster-whisper` selective recovery `clip_timestamps` compatibility fix | `1.7.1` | `CHANGELOG.md` / `RELEASES.md` |

The table records functionality by introduction release. `1.7.1` remains a candidate until its final SHA passes the release gate and its tag is created according to the release policy.
