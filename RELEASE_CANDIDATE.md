# Release Candidate — 1.5.2

## Release

- **Version:** 1.5.2
- **Candidate SHA:** updated by the final CI validation run; the release tag must point to the exact post-merge `main` SHA.
- **Previous release:** `v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`
- **Target tag:** `v1.5.2` — not created

This report is the release-gate record for PR #35. The tag must point to the exact final validated commit and must never be moved afterward.

## Scope

- Optional offline Spanish→English translation through CTranslate2 + SentencePiece.
- Pinned model revision with resource integrity validation.
- Hardened NVIDIA/CUDA detection and conservative CPU fallback.
- Managed CUDA Python runtime resources under `tools/cuda/`.
- Selective STT recovery for detected repetition/hallucination degeneration.
- No replacement of the existing audiovisual pipeline, storage architecture or naming contract.

## PRs included

- PR #35 — `feat(pr2): local translation and GPU runtime hardening`.

## Existing functionality preserved

- Common `MediaPipeline` remains authoritative.
- Existing local, cloud and rclone storage providers remain unchanged.
- Existing deterministic naming policy remains authoritative.
- Existing TTS, regeneration, scheduling, resume and deduplication flows remain available.

## Local translation

- Provider: CTranslate2 + SentencePiece.
- Model: `Prukario/opus-mt-es-en-ct2-int8`.
- Revision: `ad91ad1697ea1761111ff4c179400796d085b347`.
- Model identity is pinned; arbitrary repository/revision overrides are rejected.
- `model.bin`, `source.spm` and `target.spm` are validated by expected size and SHA-256.
- `config.json`, `shared_vocabulary.json` and `tokenizer_config.json` are required, rejected when symlinked, checked for bounded size/UTF-8 JSON and validated for the required model metadata shape.
- Preparation uses a temporary directory and atomic replacement; partial downloads are not treated as ready resources.
- Local-provider-specific options are environment variables (`LOCAL_TRANSLATION_*`), not `[local_translation]` TOML fields.

## CUDA / hardware

- `WHISPER_DEVICE=auto` and local translation `device=auto` require a verified CTranslate2 CUDA capability, not merely `nvidia-smi`.
- CUDA 12 cuBLAS and cuDNN 9 managed Python runtime dependencies are installed only through explicit interactive preparation when required.
- Managed CUDA cleanup is restricted to `tools/cuda/`.
- If CUDA capability validation fails, the affected runtime falls back to CPU `int8`.

## STT recovery

Suspicious segments are evaluated using repetition, compression, log-probability and no-speech metrics when available. Recovery retries are segment-scoped and prefer preserving context before trying context-free transcription. Logs contain diagnostic metadata rather than transcript text.

## ZIP/filesystem hardening

- ZIP traversal, absolute/UNC paths, symlinks, reserved Windows names and normalization/case collisions are rejected before extraction.
- Generated filesystem components are normalized and sanitized consistently across platforms.

## Tests

Required validation includes the complete pytest suite, configuration/provider regressions, model integrity checks, CUDA fallback branch coverage, STT quality/recovery regressions, ZIP/filesystem security tests and packaging validation.

The CUDA fallback test explicitly mocks the hardware detection and CTranslate2 capability probe so it exercises the intended failure branch rather than depending on the host runner having no GPU.

## CI

CI validates the exact PR head on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13, plus project-wide Ruff lint/security/format checks, compile checks, dependency audits, packaging, clean-wheel installation, `pip check` and entry points. Release Gate validates the candidate SHA, version metadata, distribution build and clean installation.

## Packaging

`pyproject.toml` declares `1.5.2`. Supported packaged entry points are:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

`video-translation-scheduled` is not declared and remains unsupported as a standalone entry point; scheduled execution uses `video-translation-pipeline run --scheduled`.

## Documentation

README, `docs/CONFIGURATION.md`, `docs/CUDA.md`, `docs/LOCAL_TRANSLATION.md`, `docs/RELEASES.md`, `CHANGELOG.md` and this report must describe the final 1.5.2 behavior without claiming unvalidated benchmarks or real-media A/B results.

## Known limitations

- Real GPU benchmark performance is hardware-dependent and is not a release requirement unless explicitly executed and recorded.
- The known problematic MP4 regression scenario is not stored in the repository, so no real-media A/B result is claimed by CI.
- Google Drive and rclone production credentials remain outside deterministic CI.
- Full external TTS provider execution is not a mandatory networked CI dependency.

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality | **PASS** |
| Local translation architecture | **PASS** |
| CUDA/runtime architecture | **PASS** |
| STT recovery architecture | **PASS** |
| ZIP/filesystem hardening | **PASS** |
| Tests | **PENDING FINAL SHA** |
| CI | **PENDING FINAL SHA** |
| Packaging | **PENDING FINAL SHA** |
| Documentation | **PASS AFTER THIS UPDATE** |
| Versioning | **PASS** |

## Decision

**Do not create `v1.5.2` from the PR branch.** Merge only after the final PR head is green in CI and Release Gate. After merge, validate the resulting `main` SHA and create the immutable `v1.5.2` tag/release on that exact SHA.
