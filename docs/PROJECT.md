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

The latest published release before the current candidate is `1.7.4` (`v1.7.4`). The current release candidate is `1.8.0`, associated with PR #45 and built on `main`, where PR #42 is already integrated and the `1.7.4` release baseline is preserved.

`1.8.0` refines Whisper selective recovery, separates VAD and subtitle silence thresholds, upgrades the default local translation model to pinned MADLAD-400 3B while retaining OPUS-MT, strengthens model integrity/provider tests, and keeps the reproducible `uv` foundation introduced by PR #42.

The previous releases `1.0.0` through `1.7.4` remain immutable history. `docs/RELEASES.md` is the canonical human-readable ledger for that history and the `1.8.0` candidate.

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
| Local translation model download and provider runtime fix | `1.7.2` | `tests/test_local_translation.py` / `RELEASES.md` |
| Refined Whisper recovery, dual pinned local models, uv-based reproducibility and updated TTS/WebM defaults | `1.8.0` | `RELEASE_CANDIDATE.md` / `RELEASES.md` |

The table records functionality by introduction release. `1.8.0` is the current candidate until its final SHA passes CI and Release Gate and the immutable tag is created on the resulting `main` SHA.
