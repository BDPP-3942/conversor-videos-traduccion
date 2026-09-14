# Release Candidate — 1.8.3

## Release

- **Version:** 1.8.3
- **Previous published release:** `v1.8.2` — published on 14 September 2026.
- **Target tag:** `v1.8.3` — pending final CI and Release Gate validation.
- **Candidate SHA:** the exact final `main` SHA after this documentation correction and the existing 1.8.3 implementation are validated.

Published releases `v1.8.0`, `v1.8.1` and `v1.8.2` are official release history and must remain immutable. The `1.8.3` candidate is the only current unreleased release.

## Release classification

`1.8.3` is a PATCH release. It corrects the project-managed `uv` resolution used by runtime/setup/build wrappers so that a checkout prepared by `setup_env.*` works without requiring a separate global uv installation. It does not change the processing architecture or public data contracts.

## Scope

- Add the shared POSIX resolver that prioritizes `tools/uv/uv` and falls back to `uv` from `PATH`.
- Add the equivalent Windows resolver prioritizing `tools\\uv\\uv.exe` before `PATH`.
- Make `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*` and the build scripts consume the resolved executable.
- Preserve packaged-executable precedence in unattended wrappers and the direct `.venv` Python fallback where uv is unavailable.
- Add regression coverage for local-over-PATH precedence and Windows/POSIX wrapper contracts.
- Preserve all historical release documentation while adding the 1.8.3 candidate information.

## Validation

Required before publication:

- Linux, Windows and macOS.
- Python 3.11, 3.12 and 3.13.
- Full pytest suite, including uv-resolution regression coverage.
- Ruff lint/security/format and `compileall`.
- `uv lock --check`, locked sync and `uv pip check`.
- Packaging, clean wheel installation and entry points.
- Dependency audits.
- Release Gate on the exact final `main` SHA.
- Documentation consistency checks confirming that published releases are not described as candidates and that historical release sections are retained.

## Version consistency

The candidate version must agree in:

- `pyproject.toml` → `1.8.3`.
- `config/app.toml` → `1.8.3`.
- `CHANGELOG.md` → published `1.8.2` history plus candidate `1.8.3`.
- `docs/RELEASES.md` → published releases through `1.8.2` plus candidate `1.8.3`.
- `docs/VERSIONING.md` → published releases through `1.8.2` plus candidate `1.8.3`.
- `RELEASE_SCOPE.md` → `1.8.3`.
- This file → `1.8.3`.
- `uv.lock` → project package metadata synchronized to `1.8.3`.

## Historical documentation rule

Release documentation is append-only with respect to published history. Preparing `1.8.3` MUST NOT delete, replace or downgrade the historical entries for `1.8.1` or `1.8.2`. Once a release is published, its documentation is historical and final. Only the current unreleased version may be described as a candidate.

## Decision

**Do not create `v1.8.3` until the exact final `main` SHA is green in CI and Release Gate.** After validation, create the immutable `v1.8.3` tag/release on that exact SHA and then convert the 1.8.3 candidate documentation to published-release status without removing its historical content.
