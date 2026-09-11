# Release Scope — 1.8.0

## Previous release

`v1.7.4` is the previous published release and immutable baseline. PR #42 (the uv migration) is already integrated in that baseline; `1.8.0` records the subsequent PR #45 release scope on top of it. Its GitHub Release is authoritative for the published 1.7.4 product state.

Published tags are immutable and MUST NOT be moved, deleted, or reused.

## Release classification

`1.8.0` is a **MINOR** release because it introduces compatible product functionality beyond the maintenance corrections published in `1.7.4`:

- separate Whisper VAD silence duration from subtitle split silence duration;
- context-free and prompt-free suspicious-segment recovery;
- a new pinned MADLAD-400 3B local translation fallback while preserving the existing OPUS-MT fallback;
- SentencePiece target-language handling for MADLAD;
- independent configuration and integrity validation for both local models;
- a hard local-model installation budget and integrity validation;
- reproducible `uv` dependency management across development, CI, build and audit workflows.

The public CLI/configuration architecture remains backward compatible; no MAJOR increment is warranted.

## Changes since v1.7.4

### Whisper / STT

- VAD silence remains independently configurable at `2000 ms`.
- Subtitle split silence defaults to `1000 ms` and is configured separately.
- Suspicious-segment recovery retries without the initial prompt and without previous-text conditioning to prevent prompt-amplified hallucinations.
- `clip_timestamps` remains numeric `[start, end]`.

### Local translation

- The default local fallback is upgraded to `cstr/madlad400-3b-ct2-int8`.
- The existing `Prukario/opus-mt-es-en-ct2-int8` model remains available as the lightweight compatibility option.
- MADLAD and OPUS-MT have independent model directories, repository/revision pins, artifact validation and tokenizer handling.
- The MADLAD revision is pinned and its installation is bounded by a 3,000,000,000-byte budget.
- Required artifacts are validated before activation.
- MADLAD uses the shared SentencePiece tokenizer and `<2en>` target prefix for Spanish-to-English translation.
- OPUS-MT retains `source.spm` and `target.spm` and its packaged JSON metadata path.
- CPU fallback remains available when CUDA is unavailable.
- Automatic model download remains disabled by default.

### uv / reproducibility

- `pyproject.toml` is the single Python dependency declaration source.
- `uv.lock` is the reproducible dependency resolution and is validated with `uv lock --check`.
- Development, test, packaging and audit environments use locked uv environments.
- The published wheel remains validated through clean `pip` installation.
- `pip-audit` runs from the locked audit group after removing the editable project package, so the audit covers PyPI-resolvable dependencies rather than the local source tree.

## Dependency scope

Runtime dependency declarations remain in `pyproject.toml`; the resolved graph is represented by `uv.lock`.

Runtime dependencies:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`
- `webvtt-py>=0.4,<1`
- `imageio-ffmpeg>=0.6,<1`
- `python-dotenv>=1,<2`

Optional features remain declared as PEP 621 extras and uv dependency groups.

## Version scope

- `pyproject.toml` declares `1.8.0`.
- `config/app.toml` identifies the application as `1.8.0`.
- `CHANGELOG.md` retains the complete published history during the candidate phase; the `1.8.0` entry is added at publication without removing or rewriting any historical release annotations.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.8.0` as the next release candidate.
- The `v1.8.0` tag must point to the exact validated `main` SHA after PR #45 is merged on top of the `main` baseline that already contains PR #42.

## Validation state

The exact final candidate SHA must pass CI and Release Gate before merge approval and before publication of `v1.8.0`.

The real MADLAD model benchmark remains a hardware-dependent validation step and is not replaced by deterministic CI fixtures. OPUS-MT remains independently benchmarkable for low-disk deployments.

## Tests and hardening

- Full pytest suite on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13.
- Ruff lint, Ruff security, format and `compileall`.
- `uv lock --check`, locked environment synchronization and `uv pip check`.
- Packaging, clean-wheel installation and console entry points.
- Base/Google and TTS dependency audits through the locked audit group.
- Whisper recovery and subtitle-splitting regressions.
- Local MADLAD and OPUS-MT provider, selection and integrity-validation regressions.
- Existing Unicode/filesystem, ZIP security, reprocessing and manifest regressions, including the cross-platform E2E subprocess/storage fixes.

## Release sequence

`v1.7.4` is already published and must remain unchanged. The next product release is `v1.8.0`; there is no reason to create a synthetic `v1.7.5` for the combined PR #42 + PR #45 scope.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from a PR branch.
