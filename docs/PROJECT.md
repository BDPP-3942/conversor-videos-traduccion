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
- Windows/Linux/macOS packaging and scheduler helpers;
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

The repository's published release history currently reaches `1.2.2`. The release notes establish `1.0.0` as the first product release, `1.1.0` for VTT recovery/TTS integration, `1.2.0` for naming/TTS setup improvements, `1.2.1` for TTS installation fixes, and `1.2.2` for timestamp cleanup in naming. The Python package metadata currently declares `1.0.0`; this is a repository consistency issue and must not be silently described as `1.2.2` until the package metadata is aligned.
