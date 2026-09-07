# Release Scope — 1.7.1

## Previous release

`v1.7.0` es la release publicada inmediatamente anterior y constituye el baseline funcional de esta candidata.

El tag `v1.7.0` es histórico y MUST NOT be moved, deleted, or reused.

## Historical baselines

`v1.6.0` → `a6cf0ee183a4802814fe0e061b4704e427166b85`.

`v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.

Ambas releases permanecen en la historia del proyecto, pero ninguna es la baseline inmediata de `1.7.1`.

## Changes since v1.7.0

Release `1.7.0` consolidó reprocessing/manifests, almacenamiento local multiplataforma, naming determinista y normalización Unicode, límites de filesystem y el runtime de traducción local. Release `1.7.1` es una PATCH que corrige la regresión de compatibilidad en la recuperación selectiva STT. La revisión debe partir del estado completo publicado en `v1.7.0`.

## Functional scope

- Correct `faster-whisper` `clip_timestamps` contract for selective STT recovery.
- Pass numeric `[start, end]` timestamps to `WhisperModel.transcribe()`.
- Preserve segment-scoped recovery, bounded rounds, context-preserving/context-free ordering and early stop on a healthy candidate.
- Preserve the complete `1.7.0` baseline: reprocessing/manifests, deterministic Unicode naming/filesystem behavior, local translation runtime and inherited ZIP/filesystem hardening.
- Preserve the existing audiovisual pipeline, VTT format, storage architecture and public recovery configuration.

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

- `pyproject.toml` declares `1.7.1`.
- `config/app.toml` identifies the candidate as `1.7.1`.
- `CHANGELOG.md` contains the `1.7.1` release entry before the historical `1.7.0` entry.
- `docs/RELEASES.md` records `1.7.1` as the current candidate and preserves the complete previous release history, including `1.7.0`, `1.6.0` and `1.5.1`.
- `RELEASE_CANDIDATE.md` and this file refer to `1.7.1` and use published `v1.7.0` as the immediate previous release.
- No `v1.7.1` tag exists until after merge; the tag must point to the exact resulting `main` SHA.

## Validation state

The final candidate SHA must complete CI and Release Gate successfully before merge approval. No older SHA is sufficient evidence for the final candidate.

No real-media regression or GPU benchmark is claimed unless the corresponding external artifact/run is available and recorded.

## Tests and hardening

- STT recovery regressions verify numeric `clip_timestamps` and recovered result integration.
- Existing STT retry-limit, temperature, context-order and early-stop tests remain mandatory.
- `1.7.0` reprocessing/manifests, Unicode/filesystem, translation-runtime, configuration and provider regressions remain part of the release baseline.
- ZIP/filesystem security and all project-wide quality/packaging/dependency checks remain mandatory.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
