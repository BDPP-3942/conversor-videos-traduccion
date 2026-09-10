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

### `packaging`

Builds distributions with `uv build`, verifies packaged resources, installs the wheel into a clean virtual environment using `pip`, runs `pip check` and verifies the installed console entry points. The pip installation is deliberate: it proves that the published distribution remains usable without requiring uv.

### `dependency-audit`

Creates a locked environment containing the development, Google and audit dependency groups. `pip-audit` is declared in the `audit` group and is executed as `uv run --locked --group audit pip-audit --strict`; no globally installed audit executable is assumed.

### `tts-dependency-audit`

Creates a locked environment containing the TTS extra and audit group and executes the same uv-managed `pip-audit --strict` command. This keeps the optional TTS dependency graph independently auditable.

## uv policy

`pyproject.toml` is the single declarative source for Python dependencies. `uv.lock` is committed and must pass `uv lock --check` on every CI/release candidate. CI uses `uv sync --locked` so the runner cannot silently resolve a different dependency graph.

The project does not require uv for the final wheel consumer. The clean-wheel compatibility gate uses pip explicitly. Portable CUDA runtime installation also retains its deliberate pip fallback for executables that do not ship with uv.

## Release Gate

`release-gate.yml` validates the exact candidate SHA, the static project version, the application version in `config/app.toml`, the `CHANGELOG.md` release heading, `docs/RELEASES.md`, packaged resources, clean wheel installation and source compilation.

For the `1.7.4` candidate, all versioning documents must identify the same candidate and the release tag must remain absent during the manual release invocation. The final tag `v1.7.4` must be created only on the exact `main` SHA resulting from the validated merge.

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
uv run --locked --group audit pip-audit --strict

uv sync --locked --extra tts --group audit
uv run --locked --group audit pip-audit --strict
```

For local translation specifically, the target environment should additionally run:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/manage_local_translation.py download
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

The real-model benchmark is hardware-specific; CI uses deterministic doubles for the model download/runtime regressions so the production model is not downloaded on every runner.

The CI workflow is authoritative for the exact commands and matrix.
