# Release Scope — 1.8.3

## Previous release state

`v1.8.0` is the last published release and remains immutable. The `1.8.2` candidate state is superseded by this `1.8.3` corrective candidate.

## Release classification

`1.8.3` is a **PATCH** release. The scope fixes a regression in the project-managed uv execution contract without changing the audiovisual processing architecture or public data contracts.

## Project-managed uv correction

The setup wrappers already support a managed executable under `tools/uv/` when no global uv is installed. The regression was that several consumer scripts still required `uv`/`uv.exe` to be discoverable through `PATH`.

The correction introduces:

- `scripts/lib/resolve_uv.sh` for POSIX.
- `scripts/lib/resolve_uv.bat` for Windows.

Both resolvers apply the same policy:

1. project-managed uv;
2. uv from `PATH`;
3. setup-only bootstrap when neither is available.

Affected consumers:

- `run_local.*`;
- `run_unattended.*`;
- `setup_rclone.*`;
- `setup_google.*`;
- `build_linux.sh`;
- `build_windows.bat`.

Unattended execution continues to prefer packaged executables and retains the direct Python fallback.

## Tests and CI

`tests/test_uv_resolution_contract.py` covers:

- project-managed uv precedence over PATH;
- POSIX wrapper integration with the shared resolver;
- Windows wrapper integration with the shared resolver;
- build/setup command invocation through the resolved executable;
- unattended packaged-executable priority and fallback behavior;
- prevention of regressions that make a global uv lookup mandatory.

The existing CI matrix remains Linux/Windows/macOS with Python 3.11, 3.12 and 3.13.

## Documentation

Release behavior is documented in `CHANGELOG.md`, `RELEASE_CANDIDATE.md`, `docs/UV_MIGRATION.md`, `docs/VERSIONING.md`, `docs/RELEASES.md`, `docs/PROJECT.md` and `docs/CI_CD.md`.

## Version consistency

- `pyproject.toml` → `1.8.3`.
- `config/app.toml` → `1.8.3`.
- release-control documents → `1.8.3`.

## Release gate

Before publication, validate the exact final merge SHA with the complete test matrix, lint/security/format, compileall, lockfile checks, packaging, audits and explicit wrapper execution with project-managed uv present and global uv absent from PATH.
