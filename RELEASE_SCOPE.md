# Release Scope — 1.6.1

## Previous release

`v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.

The tag is historical and MUST NOT be moved, deleted, or reused.

## Changes since v1.5.1

The `1.6.x` line introduced local translation, GPU/runtime hardening and selective STT recovery. Release `1.6.1` is a PATCH correction for a compatibility regression in that STT recovery path.

## Functional scope

- Correct `faster-whisper` `clip_timestamps` contract for selective STT recovery.
- Pass numeric `[start, end]` timestamps to `WhisperModel.transcribe()`.
- Preserve segment-scoped recovery, bounded rounds, context-preserving/context-free ordering and early stop on a healthy candidate.
- Preserve the existing audiovisual pipeline, VTT format, storage architecture and public recovery configuration.
- Keep the `1.6.0` local-translation, CUDA/runtime and ZIP/filesystem hardening baseline unchanged.

## Dependency scope

The runtime dependency contract for this release is:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`
- `webvtt-py>=0.4,<1`
- `imageio-ffmpeg>=0.6,<1`
- `python-dotenv>=1,<2`

`requirements.txt` and `pyproject.toml` must remain aligned. Derived requirements files inherit from `requirements.txt`.

## Configuration scope

The canonical application configuration remains `config/app.toml`, with environment overrides. This release does not introduce a new TOML configuration key for the STT recovery fix. The existing `whisper_recovery_retries` and `whisper_recovery_temperatures` contract remains unchanged.

## Version scope

- `pyproject.toml` declares `1.6.1`.
- `CHANGELOG.md` contains the `1.6.1` release entry before the historical `1.6.0` entry.
- `docs/RELEASES.md` records `1.6.1` as the current candidate and preserves the complete previous release history.
- `RELEASE_CANDIDATE.md` and this file refer to `1.6.1`.
- No `v1.6.1` tag exists until after merge; the tag must point to the exact resulting `main` SHA.

## Validation state

The final candidate SHA must complete CI and Release Gate successfully before merge approval. No older SHA is sufficient evidence for the final candidate.

No real-media regression or GPU benchmark is claimed unless the corresponding external artifact/run is available and recorded.

## Tests and hardening

- STT recovery regressions verify numeric `clip_timestamps` and recovered result integration.
- Existing STT retry-limit, temperature, context-order and early-stop tests remain mandatory.
- ZIP/filesystem security and all project-wide quality/packaging/dependency checks remain mandatory.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
