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

## Version evidence

The current `main` branch declares package version `1.2.2` in `pyproject.toml`, matching the latest published GitHub release/tag `1.2.2`.

The verified release history establishes:

| Capability | First verified product release | Evidence |
|---|---:|---|
| Core audiovisual pipeline, STT, VTT, translation, storage, resume/idempotency, conservative deduplication, TTS, scheduling and packaging | `1.0.0` | `CHANGELOG.md` / release history |
| VTT recovery/repair and integrated synchronized TTS | `1.1.0` | `CHANGELOG.md` / release history |
| Naming improvements and TTS asset bootstrap | `1.2.0` | `CHANGELOG.md` / release history |
| TTS installation fix | `1.2.1` | release history |
| Timestamp cleanup in naming | `1.2.2` | release history |

The table records only functionality for which the repository's release history provides explicit evidence; it does not infer introduction dates from source-code presence alone.
