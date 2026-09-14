# Release Scope — 1.8.3

## Previous release state

`v1.8.2` is the previous published release and immutable baseline. `v1.8.1` and `v1.8.2` are official published releases; neither is a candidate or superseded preparation state. The only current unreleased version is `1.8.3`.

Published release history:

- `v1.8.2` → MADLAD model download and Hugging Face revision fix.
- `v1.8.1` → Local uv bootstrap and optional local translation setup.
- `v1.8.0` → Whisper recovery and local translation.

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

## Documentation and historical integrity

Release documentation is cumulative. The `1.8.3` changes add a new candidate section and MUST NOT remove or downgrade historical content for `1.8.1` or `1.8.2`.

The release-control documents must consistently distinguish:

- published releases: `1.8.0`, `1.8.1`, `1.8.2`;
- current candidate: `1.8.3`;
- no other version as an active candidate.

Release behavior is documented in `CHANGELOG.md`, `RELEASE_CANDIDATE.md`, `docs/UV_MIGRATION.md`, `docs/VERSIONING.md`, `docs/RELEASES.md`, `docs/PROJECT.md` and `docs/CI_CD.md`.

## Version consistency

- `pyproject.toml` → `1.8.3`.
- `config/app.toml` → `1.8.3`.
- `CHANGELOG.md` → published history through `1.8.2` plus candidate `1.8.3`.
- `docs/RELEASES.md` → published history through `1.8.2` plus candidate `1.8.3`.
- `docs/VERSIONING.md` → published history through `1.8.2` plus candidate `1.8.3`.
- `RELEASE_CANDIDATE.md` → `1.8.3`.
- this file → `1.8.3`.

## Release gate

Before publication, validate the exact final merge SHA with the complete test matrix, lint/security/format, compileall, lockfile checks, packaging, audits and explicit wrapper execution with project-managed uv present and global uv absent from PATH.
