# Release Scope — 1.8.2

## Previous release

`v1.8.0` is the previous published release and immutable baseline. Published tags are immutable and MUST NOT be moved, deleted, or reused.

`1.8.1` was an unfinished candidate and is not a published release; its release-preparation documents are superseded by this corrective `1.8.2` candidate.

## Release classification

`1.8.2` is a **PATCH** release because the scope corrects the local-model resource pin, validation/tests, CI formatting/consistency and release documentation without changing the processing architecture or public data contracts.

## Changes since v1.8.0

### MADLAD Hugging Face resource correction

- MADLAD-400 3B CT2 INT8 is pinned to `cstr/madlad400-3b-ct2-int8@fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- The tokenizer artifact is `spiece.model`; the old `sentencepiece.model` lookup is invalid for the pinned repository state.
- The verified `spiece.model` SHA-256 is `ef11ac9a22c7503492f56d48dce53be20e339b63605983e9f27d2cd0e0f3922c` and its expected size is `4,427,844` bytes.
- OPUS-MT remains an independent lightweight model with its existing repository and revision.
- Download diagnostics distinguish a missing artifact/revision (404) from authentication/authorization failures (401/403).

### Tests and CI

- MADLAD unit-test fixtures now use byte counts matching their fixture payloads.
- The local-translation regression suite covers the pinned revision, tokenizer filename, integrity validation, target-language prefix and 404 diagnostics.
- `uv` quality checks must run the tests before lint/format/build gates and must not hide failures with `continue-on-error`.

### Release metadata and documentation

- `pyproject.toml` and `config/app.toml` identify version `1.8.2`.
- Release candidate, scope, changelog, versioning and release-history documentation identify `1.8.2` as the next release.
- No historical release tag is modified or reused.

## Dependency scope

Runtime dependency declarations remain in `pyproject.toml`; the resolved graph is represented by `uv.lock`.

Runtime dependencies remain:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`
- `webvtt-py>=0.4,<1`
- `imageio-ffmpeg>=0.6,<1`
- `python-dotenv>=1,<2`

Optional features remain declared as PEP 621 extras and uv dependency groups.

## Version scope

- `pyproject.toml` declares `1.8.2`.
- `config/app.toml` identifies the application as `1.8.2`.
- `CHANGELOG.md` receives the `1.8.2` candidate entry; the published `1.8.0` history remains unchanged.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.8.2` as the next release candidate.
- The `v1.8.2` tag must point to the exact validated `main` SHA after this PR is merged.

## Validation state

The exact final candidate SHA must pass CI and Release Gate before merge approval and before publication of `v1.8.2`.

The real MADLAD model benchmark remains a hardware-dependent validation step and is not replaced by deterministic CI fixtures.

## Tests and hardening

- Full pytest suite on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13.
- Ruff lint, Ruff security, format and `compileall`.
- `uv lock --check`, locked environment synchronization and `uv pip check`.
- Packaging, clean-wheel installation and console entry points.
- Base/Google and TTS dependency audits through the locked audit group.
- Regression coverage for setup-script syntax and documented setup behavior where applicable.
- Existing Unicode/filesystem, ZIP security, reprocessing, manifest, Whisper recovery and local translation regressions.

## Release sequence

`v1.8.0` is already published and must remain unchanged. `1.8.1` is not published. The next product release is `v1.8.2`.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No change to the public processing/storage contracts.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No automatic local translation download unless `--local-translation` is explicitly supplied.
- No release tag creation from a PR branch.
