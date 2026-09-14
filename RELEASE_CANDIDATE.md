# Release Candidate — 1.8.1

## Release

- **Version:** 1.8.1
- **Previous published release:** `v1.8.0` — published on 13 September 2026.
- **Target tag:** `v1.8.1` — pending final CI, Release Gate and merge validation.
- **Candidate SHA:** must be the exact final `main` SHA after this PR is merged and validated.

`v1.8.0` is already a published GitHub Release. It is historical state, not a candidate, and its tag must not be recreated or moved.

## Release classification

`1.8.1` is a PATCH release. The scope is backward-compatible setup, resource preparation and documentation maintenance.

## Scope

- Bootstrap a project-managed `tools/uv/uv` or `tools\uv\uv.exe` when no system uv is available.
- Prefer an existing project-managed uv copy, then a system uv from `PATH`, before bootstrapping a new local copy.
- Use the official uv unmanaged installer without modifying user shell profiles.
- Route Python installation, virtual-environment creation, dependency synchronization and setup commands through the resolved uv executable.
- Add `--local-translation` to both setup scripts so the pinned local translation model can be prepared in the same setup process when explicitly requested.
- Preserve `uv run python scripts/manage_local_translation.py download` for deferred model installation.
- Keep the default local model, revisions, integrity checks and storage contract unchanged.

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

- `pyproject.toml` → `1.8.1`.
- `config/app.toml` → `1.8.1`.
- `docs/RELEASES.md` → published `1.8.0` plus candidate `1.8.1`.
- `docs/VERSIONING.md` → published `1.8.0` plus candidate `1.8.1`.
- `RELEASE_SCOPE.md` → `1.8.1`.
- This file → `1.8.1`.
- `uv.lock` → project package metadata synchronized to `1.8.1`.

## Decision

**Do not merge or create `v1.8.1` until the final candidate SHA is green in CI and Release Gate.** After merge, validate `main` again and create the immutable `v1.8.1` tag/release on that exact SHA.
