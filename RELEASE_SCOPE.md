# Release Scope — 1.8.1

## Previous release

`v1.8.0` is the previous published release and immutable baseline. Published tags are immutable and MUST NOT be moved, deleted, or reused.

## Release classification

`1.8.1` is a **PATCH** release because the scope improves setup, resource preparation and documentation without changing the processing architecture or public data contracts.

## Changes since v1.8.0

### Project-managed uv bootstrap

- `scripts/setup_env.sh` now prefers an existing project-managed `tools/uv/uv`, then a system `uv` from `PATH`, and finally bootstraps uv locally when neither exists.
- The local bootstrap uses the official uv installer in unmanaged mode so shell profiles are not modified.
- `scripts/setup_env.bat` provides the equivalent Windows behavior with `tools\uv\uv.exe`.
- The project-managed uv executable is ignored by Git and is never committed as a host-specific binary.
- Python, the project `.venv`, dependency synchronization and all subsequent setup commands use the resolved uv executable.

### Local translation setup

- Both setup scripts accept `--local-translation`.
- When enabled, the setup completes the normal environment preparation and then executes the existing validated local-model download flow.
- The option is deliberately opt-in because the default MADLAD-400 3B model is approximately 2.95 GB.
- Deferred installation remains fully supported with:

```bash
uv run python scripts/manage_local_translation.py download
```

- Model selection, repository/revision pins, integrity validation and storage layout remain unchanged.

### Documentation

- Installation documentation now explains the uv bootstrap decision tree and the optional model download.
- Release/versioning documents identify `1.8.1` as the current patch candidate.
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

- `pyproject.toml` declares `1.8.1`.
- `config/app.toml` identifies the application as `1.8.1`.
- `CHANGELOG.md` keeps the immutable published history and receives the `1.8.1` entry as part of this candidate because the previous `1.8.0` release is already published.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.8.1` as the next release candidate.
- The `v1.8.1` tag must point to the exact validated `main` SHA after this PR is merged.

## Validation state

The exact final candidate SHA must pass CI and Release Gate before merge approval and before publication of `v1.8.1`.

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

`v1.8.0` is already published and must remain unchanged. The next product release is `v1.8.1`; no intermediate `1.8.0.x` release is required.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No change to model/revision pins.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No automatic local translation download unless `--local-translation` is explicitly supplied.
- No release tag creation from a PR branch.
