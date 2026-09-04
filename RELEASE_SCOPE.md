# Release Scope — 1.5.2

## Previous release

`v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.

The tag is historical and MUST NOT be moved, deleted, or reused.

## Changes since v1.5.1

PR #35 introduces optional offline local translation, hardens GPU/runtime selection and improves integrity and recovery behavior without replacing the existing media pipeline.

## Functional scope

- Local Spanish→English translation through CTranslate2 + SentencePiece.
- Pinned model repository/revision with deterministic validation of the core model artifacts and structural validation of required JSON metadata.
- Explicit model preparation/status/cleanup tooling.
- NVIDIA/CUDA capability detection based on actual CTranslate2 support rather than GPU presence alone.
- Managed CUDA Python runtime resources for cuBLAS CUDA 12 and cuDNN 9.
- Conservative CUDA→CPU fallback.
- Selective STT recovery for suspicious repetition/hallucination segments.
- ZIP and filesystem normalization/security hardening remains part of the release baseline.

## Configuration scope

The canonical application configuration remains `config/app.toml`, with environment overrides. Local-translation-specific settings use the `LOCAL_TRANSLATION_*` environment variables documented in `.env.example`, `docs/CONFIGURATION.md` and `docs/LOCAL_TRANSLATION.md`. There is deliberately no duplicate `[local_translation]` TOML section.

The pinned model identity is not user-selectable: `LOCAL_TRANSLATION_MODEL_ID` and `LOCAL_TRANSLATION_MODEL_REVISION` must match the project constants.

## Validation state

- `pyproject.toml` declares version `1.5.2`.
- Release documentation identifies `v1.5.1` as the previous published release.
- CI must validate the final release candidate on the exact final commit SHA.
- No `v1.5.2` tag exists until the release gate is satisfied.
- No real-media regression or GPU benchmark is claimed unless the corresponding external artifact/run is available and recorded.

## Tests and hardening

- Model status rejects missing resources, incorrect core hashes/sizes, unsafe metadata and malformed required JSON metadata.
- CUDA fallback tests mock hardware detection and the CTranslate2 capability probe so the intended failure branch is exercised deterministically.
- Provider configuration tests cover the environment-driven local translation settings.
- ZIP/filesystem security and STT recovery regressions remain mandatory.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
