# CI/CD

GitHub Actions runs on pushes to `main` and release branches, and on pull requests targeting `main`.

The workflow checks out the exact submitted PR head SHA. Concurrency cancellation prevents obsolete runs from consuming resources, but an older successful SHA is never evidence for a newer candidate.

## CI jobs

### `quality`

Runs once on `ubuntu-latest` with Python 3.13. It provisions the locked development environment with uv and checks:

- `uv lock --check`;
- locked dependency consistency with `uv pip check`;
- Ruff imports/unused imports, lint, security and formatting;
- Python bytecode compilation.

### `tests`

Runs on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13. Each runner executes `uv sync --locked`, `uv pip check`, the complete pytest suite except the wheel-only packaging test, installed entry points and the platform-specific wrapper checks.

The platform matrix is intentionally retained because filesystem, process, native-library and path-normalization behavior cannot be proven on one operating system.

The release E2E suite includes deterministic STT/translation adapters and isolated storage per subprocess. Its ZIP/input fixture and Windows/POSIX path handling are part of the cross-platform release validation rather than optional local-only checks.

### `packaging`

Builds distributions with `uv build`, verifies packaged resources, installs the wheel into a clean virtual environment using `pip`, runs `pip check` and verifies the installed console entry points. The pip installation is deliberate: it proves that the published distribution remains usable without requiring uv.

### `dependency-audit`

Creates a locked environment containing the development, Google and audit dependency groups. `pip-audit` is declared in the `audit` group and is executed as `uv run --locked --no-sync --group audit pip-audit --strict` after removing the editable project package.

### `tts-dependency-audit`

Creates a locked environment containing the TTS extra and audit group and executes the same uv-managed `pip-audit --strict` command. This keeps the optional TTS dependency graph independently auditable.

## uv policy

`pyproject.toml` is the single declarative source for Python dependencies. `uv.lock` is committed and must pass `uv lock --check` on every CI/release validation. CI uses `uv sync --locked` so the runner cannot silently resolve a different dependency graph.

The project does not require uv for the final wheel consumer. The clean-wheel compatibility gate uses pip explicitly. Portable CUDA runtime installation also retains its deliberate pip fallback for executables that do not ship with uv.

For source-checkout scripts, the project-managed uv contract is:

1. `tools/uv/uv` on POSIX or `tools\\uv\\uv.exe` on Windows when present;
2. system `uv`/`uv.exe` from `PATH` as fallback;
3. only the setup wrappers bootstrap a missing copy into `tools/uv/`.

The shared resolvers are `scripts/lib/resolve_uv.sh` and `scripts/lib/resolve_uv.bat`. Runtime/setup/build wrappers consume the resolved executable instead of making a global PATH lookup mandatory.

## Published releases

### Release 1.8.2

`1.8.2` is a published PATCH release. Its validation covered the exact source SHA, static project/application versions, release metadata, packaged resources, clean wheel installation, source compilation, tests and dependency audits. The `v1.8.2` tag is immutable.

### Release 1.8.1

`1.8.1` is a published PATCH release. Its validation covered the project-managed uv bootstrap, optional local translation preparation, the complete platform/version matrix, packaging and Release Gate. The `v1.8.1` tag is immutable.

### Release 1.8.0

`1.8.0` is a published MINOR release. Subsequent development must use the next version rather than rewriting published release metadata.

## Current candidate: 1.8.3

`1.8.3` is the only current unreleased candidate. The Release Gate must validate the complete Linux/Windows/macOS matrix, Python 3.11/3.12/3.13, pytest, lint/security/format, compileall, lockfile checks, packaging, audits and wrapper behavior before `v1.8.3` is published.

The Windows wrapper test must cover the case where `tools\\uv\\uv.exe` exists even when no global `uv.exe` is available on `PATH`. POSIX regression coverage must verify the equivalent `tools/uv/uv` precedence.

Historical release documentation is cumulative: preparing `1.8.3` must not remove or downgrade the release history for `1.8.1` or `1.8.2`.

## Local parity

At minimum, run the same project checks locally through uv:

```bash
uv lock --check
uv sync --locked --extra google --group dev
uv pip check
uv run pytest -q
uv run ruff check .
uv run ruff check . --select S
uv run ruff format --check .
uv run python -m compileall .
uv build
```

For dependency auditing:

```bash
uv sync --locked --extra google --group dev --group audit
uv run --locked --no-sync --group audit pip-audit --strict

uv sync --locked --extra tts --group audit
uv run --locked --no-sync --group audit pip-audit --strict
```

For local translation specifically, the target environment should additionally run:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/manage_local_translation.py download
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

Both supported local models remain available: MADLAD-400 3B is the default quality-oriented model, while OPUS-MT is retained for low-disk/compatibility deployments. The real-model benchmark is hardware-specific; CI uses deterministic doubles for model download/runtime regressions so the production model is not downloaded on every runner.

The CI workflow is authoritative for the exact commands and matrix.
