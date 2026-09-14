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

## Current published release

The current product release is `1.8.2` (`v1.8.2`). It follows the published `1.8.1` release and contains the MADLAD resource, tokenizer, fixture and Hugging Face diagnostics correction.

The current unreleased candidate is `1.8.3`. It corrects the project-managed `uv` resolution contract used by runtime/setup/build wrappers and does not replace or supersede the published `1.8.1` or `1.8.2` history.

Published releases `1.0.0` through `1.8.2` remain immutable. `docs/RELEASES.md`, `docs/VERSIONING.md` and `CHANGELOG.md` retain the complete release ledger; only `1.8.3` is an active candidate.

See [RELEASES.md](RELEASES.md) for historical release tracking and [../RELEASE_CANDIDATE.md](../RELEASE_CANDIDATE.md) for the current publication checklist.

## Verified release evidence

| Capability | First verified product release | Evidence |
| --- | ---: | --- |
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
| Local translation model download and provider runtime fix | `1.7.2` | `CHANGELOG.md` / `RELEASES.md` |
| Local translation metadata bootstrap | `1.7.3` | `CHANGELOG.md` / `RELEASES.md` |
| Shared vocabulary validation and reproducible uv migration | `1.7.4` | `CHANGELOG.md` / `RELEASES.md` |
| Refined Whisper recovery, dual pinned local models and updated TTS/WebM defaults | `1.8.0` | published GitHub release |
| Project-managed uv bootstrap and optional local translation preparation | `1.8.1` | published GitHub release |
| MADLAD resource, tokenizer and Hugging Face diagnostics correction | `1.8.2` | published GitHub release |
| Project-managed uv wrapper resolution across POSIX/Windows | `1.8.3` | current release candidate |

## Release history

- `v1.8.2` — official published release; immutable.
- `v1.8.1` — official published release; immutable.
- `v1.8.0` — official published release; immutable.
- `1.8.3` — current and only active release candidate.
- Earlier releases from `1.0.0` through `1.7.4` remain historical and immutable.

Release-control documents must never rewrite a published release into a candidate state. New release work is appended as the next candidate.
