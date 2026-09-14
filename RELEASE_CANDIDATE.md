# Release Candidate — 1.8.2

## Release

- **Version:** 1.8.2
- **Previous published release:** `v1.8.0` — published on 13 September 2026.
- **Target tag:** `v1.8.2` — pending final CI, Release Gate and merge validation.
- **Candidate SHA:** must be the exact final `main` SHA after this PR is merged and validated.

`v1.8.0` is a published GitHub Release and remains immutable. `1.8.1` is not published; this candidate supersedes the unfinished 1.8.1 preparation because the MADLAD correction is required for a releasable state.

## Release classification

`1.8.2` is a PATCH release. It corrects the pinned MADLAD Hugging Face resource, local-model validation/tests, setup/release documentation and CI formatting/consistency without changing the processing architecture or public data contracts.

## Scope

- Pin MADLAD-400 3B CT2 INT8 to the verified revision `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Use the repository's actual tokenizer artifact `spiece.model` instead of the nonexistent `sentencepiece.model`.
- Preserve the independent OPUS-MT definition and revision.
- Keep SHA-256 and expected-size validation for the managed local model.
- Make Hugging Face download diagnostics distinguish a missing file/revision (`404`) from authentication/authorization failures (`401`/`403`).
- Correct MADLAD unit-test fixtures so their expected byte sizes match the fixture payloads.
- Align project/application/release metadata on `1.8.2` and prepare the release documentation.
- Keep `uv run python scripts/manage_local_translation.py download` as the explicit deferred model-installation command.

## Validation

Required before publication:

- Linux, Windows and macOS.
- Python 3.11, 3.12 and 3.13.
- Full pytest suite, including the cross-platform release E2E tests.
- Ruff lint/security/format and `compileall`.
- `uv lock --check`, locked sync and `uv pip check`.
- Packaging, clean wheel installation and entry points.
- Dependency audits.
- Release Gate on the exact final SHA.
- Real local-model preparation/benchmark remains a hardware-dependent validation step and is not substituted by CI fixtures.

## Version consistency

The candidate version must agree in:

- `pyproject.toml` → `1.8.2`.
- `config/app.toml` → `1.8.2`.
- `docs/RELEASES.md` → published `1.8.0` plus candidate `1.8.2`.
- `docs/VERSIONING.md` → published `1.8.0` plus candidate `1.8.2`.
- `RELEASE_SCOPE.md` → `1.8.2`.
- This file → `1.8.2`.
- `uv.lock` → project package metadata synchronized to `1.8.2`.

## Decision

**Do not merge or create `v1.8.2` until the final candidate SHA is green in CI and Release Gate.** After merge, validate `main` again and create the immutable `v1.8.2` tag/release on that exact SHA.
