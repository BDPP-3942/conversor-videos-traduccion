# Release Candidate — 1.8.3

## Release

- **Version:** 1.8.3
- **Previous published release:** `v1.8.0` — the repository currently carries `1.8.2` as an unreleased candidate state.
- **Target tag:** `v1.8.3` — pending final CI, Release Gate and merge validation.
- **Candidate SHA:** must be the exact final `main` SHA after this candidate is merged and validated.

Published tags remain immutable. The `1.8.2` candidate state is superseded by this `1.8.3` candidate because the newly identified `uv` wrapper regression prevents the documented no-global-uv setup from working through several runtime/setup entry points.

## Release classification

`1.8.3` is a PATCH release. It corrects the project-managed `uv` resolution contract without changing the processing architecture or public data contracts.

## Scope

### Project-managed uv resolution

- Add a shared POSIX resolver at `scripts/lib/resolve_uv.sh`.
- Add the equivalent Windows resolver at `scripts/lib/resolve_uv.bat`.
- Always prefer `tools/uv/uv` or `tools\\uv\\uv.exe` when present.
- Fall back to `uv`/`uv.exe` available through `PATH`.
- Keep the bootstrap behavior in `setup_env.*`: when neither source exists, install the managed copy under `tools/uv/`.

### Affected entry points

- `run_local.*`
- `run_unattended.*`
- `setup_rclone.*`
- `setup_google.*`
- `build_linux.sh`
- `build_windows.bat`

Packaged executables keep their existing priority in unattended execution. The direct `.venv` Python fallback remains available when no uv executable can be resolved.

### Regression tests

- Verify resolver priority: project-managed uv before `PATH`.
- Verify all POSIX wrappers use the shared resolver.
- Verify all Windows wrappers use the shared resolver.
- Verify unattended wrappers retain packaged-executable priority and Python fallback.
- Verify wrappers no longer make global `command -v uv` / `where uv.exe` a mandatory precondition.

## Documentation

The release documentation records the corrected contract in:

- `CHANGELOG.md`
- `docs/UV_MIGRATION.md`
- `docs/VERSIONING.md`
- `docs/RELEASES.md`
- `docs/PROJECT.md`
- `docs/CI_CD.md`
- `RELEASE_SCOPE.md`

## Validation

Required before publication:

- Linux, Windows and macOS.
- Python 3.11, 3.12 and 3.13.
- Full pytest suite.
- Ruff lint/security/format and `compileall`.
- `uv lock --check`, locked sync and `uv pip check`.
- Packaging and clean wheel installation.
- Dependency audits.
- Real Windows and POSIX wrapper execution with project-managed uv present and global uv absent from `PATH`.
- Release Gate on the exact final SHA.

## Version consistency

The candidate version must agree in:

- `pyproject.toml` → `1.8.3`.
- `config/app.toml` → `1.8.3`.
- `CHANGELOG.md` → `1.8.3` candidate.
- `RELEASE_SCOPE.md` → `1.8.3` candidate.
- `docs/VERSIONING.md` → `1.8.3` candidate.
- `docs/RELEASES.md` → `1.8.3` candidate.
