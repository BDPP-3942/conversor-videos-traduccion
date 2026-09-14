# CI/CD

GitHub Actions runs on pushes to `main` and release branches and on pull requests targeting `main`.

## CI jobs

### Quality

The quality job provisions the locked development environment with uv and checks `uv lock --check`, `uv pip check`, Ruff imports/lint/security/formatting and Python compilation.

### Tests

The test matrix runs on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13. It executes locked synchronization, dependency checks, the pytest suite, installed entry points and platform-specific wrapper validation.

The matrix is required because filesystem, process, native-library and path behavior cannot be proven on one operating system.

### Packaging

Distributions are built with uv, checked for packaged resources, installed into a clean environment with pip and validated with `pip check` and the published console entry points. The pip gate deliberately proves that uv is not a runtime requirement of the wheel.

### Dependency audits

Audit jobs use locked uv environments and `pip-audit --strict` for the development/Google and TTS dependency graphs.

## uv policy

`pyproject.toml` is the single declarative dependency source and `uv.lock` is the reproducible graph. CI uses `uv sync --locked` and `uv lock --check`.

For source-checkout scripts, uv resolution follows the same contract on every platform:

1. project-managed `tools/uv/uv` on POSIX or `tools\\uv\\uv.exe` on Windows;
2. system `uv`/`uv.exe` from `PATH`;
3. only the setup wrappers bootstrap a missing copy into `tools/uv/`.

The shared resolvers are `scripts/lib/resolve_uv.sh` and `scripts/lib/resolve_uv.bat`. The regression suite `tests/test_uv_resolution_contract.py` prevents wrappers from reverting to a mandatory global `PATH` lookup.

The final wheel does not require uv. CUDA runtime installation intentionally retains its pip fallback for packaged environments that do not ship with uv.

## Release 1.8.3

`1.8.3` is a PATCH candidate for the project-managed uv wrapper regression. The Release Gate must validate the complete Linux/Windows/macOS matrix, Python 3.11/3.12/3.13, pytest, lint/security/format, compileall, lockfile checks, packaging, audits and wrapper behavior before the tag `v1.8.3` is published.

The Windows wrapper test must cover the case where `tools\\uv\\uv.exe` exists even when no global `uv.exe` is available on `PATH`. POSIX regression coverage must verify the equivalent `tools/uv/uv` precedence.

## Release validation rule

A successful workflow for an older SHA never validates a newer candidate. The release tag must identify exactly the SHA that passed the complete Release Gate after merge.
