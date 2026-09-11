# UV migration — historical preview

This document is retained as the historical design record for the migration from the pip/requirements development workflow to `uv`. The migration was implemented through PR #42 and is already integrated in `main`; it forms part of the published `1.7.4` baseline. The document is no longer a proposal or a pending production migration.

## Target architecture

```text
pyproject.toml
  ├─ runtime dependencies
  ├─ optional extras: google / tts / package
  └─ dev dependency group
          │
          ▼
       uv.lock
          │
          ├─ local .venv
          ├─ CI: uv sync --locked
          └─ packaging: uv build
                    │
                    ▼
                dist/*.whl
                    │
                    ▼
          clean pip install gate
```

`pyproject.toml` remains the declaration source. `uv.lock` becomes the resolved, reproducible dependency graph and must be committed once the migration is implemented. Published wheels remain standard Python wheels and must continue to install with pip; end users must not be required to install uv.

## Historical preview implemented by PR #42

The historical `.github/workflows/uv-preview.yml` demonstrated the intended CI sequence before the production migration. The authoritative current workflow is `.github/workflows/ci.yml`.

1. Install a controlled uv action release.
2. Provision Python through uv.
3. Resolve the dependency graph.
4. Synchronize the development environment with project extras.
5. Run dependency checks, tests, Ruff and packaging through uv.
6. Install the resulting wheel with pip in a clean environment and run the existing entry-point compatibility checks.

The migration is now complete: `uv.lock` is committed and current CI uses `uv lock --check` and locked synchronization. The remaining pip usage is deliberate for clean-wheel compatibility and selected bootstrap paths.

## Recommended repository migration

### 1. Dependency declaration

Keep normal runtime dependencies in `[project].dependencies` and user-facing optional features in `[project.optional-dependencies]`:

- `google`: Google authentication support.
- `tts`: Kokoro runtime.
- `package`: PyInstaller tooling if it remains an installation-time requirement.

Move development-only tooling to `[dependency-groups].dev` when the final uv configuration is selected. Avoid duplicating the same dependency graph in `requirements*.txt`.

### 2. Locking and local environments

Commit `uv.lock` and make `.venv` the canonical project environment. The intended commands are:

```bash
uv sync
uv sync --extra google
uv sync --extra tts
uv sync --extra package
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

Use `uv lock --upgrade` only as an explicit dependency-upgrade operation. CI should use the committed lockfile rather than resolving a new graph on every run.

### 3. Installer scripts

`setup_env.sh` and `setup_env.bat` should stop creating an independent pip-managed environment and delegate to `uv sync`. Existing flags should map to extras instead of separate requirements files.

Examples:

```text
base install       -> uv sync
Google support     -> uv sync --extra google
TTS support        -> uv sync --extra tts
packaging tools    -> uv sync --extra package
```

The scripts should check that uv exists and emit one clear installation message when it does not. They should not install uv implicitly during normal application execution.

### 4. run_local and schedulers

`run_local.sh` / `run_local.bat` should continue to be thin dispatchers. They should invoke the project through `uv run` only when operating from a source checkout, preserving all existing arguments and subcommands.

Schedulers should use the same canonical project command rather than installing dependencies themselves. A scheduler entry should conceptually become:

```text
uv run video-translation-pipeline --scheduled ...
```

The production design should avoid `uv sync` on every scheduled execution. Synchronization belongs to deployment/bootstrap; execution should use an already prepared environment.

### 5. Build and executable creation

Build scripts should replace `python -m pip install -r requirements-dev.txt` with a single synchronized environment and invoke PyInstaller through that environment, for example:

```text
uv sync --extra package
uv run pyinstaller ...
```

This keeps the executable build tied to the same lockfile as tests and local development.

### 6. TTS and CUDA installers

Do **not** perform a mechanical `pip -> uv` replacement everywhere.

`setup_tts.py` should eventually stop installing Python dependencies itself. The bootstrap script should synchronize `tts` dependencies, while the Python script should only download/validate TTS model assets.

`src/cuda_runtime.py` is a separate high-risk case because it installs NVIDIA runtime wheels dynamically into a managed runtime directory. It should remain unchanged in the first uv migration unless a dedicated design proves that uv can preserve its isolated runtime semantics and cross-platform behavior.

### 7. CI adaptation

The final CI should use uv for:

- environment provisioning;
- dependency synchronization;
- test execution;
- Ruff execution;
- compile checks;
- package building;
- dependency resolution consistency.

The CI should retain pip for one deliberately isolated compatibility test: install the built wheel into a fresh environment with pip and run `pip check` plus the published console entry points. This proves that uv has not accidentally made the distributable package uv-specific.

The existing `pip-audit` policy can remain independently of the project installer migration.

### 8. Requirements files

After a repository-wide audit confirms there are no external consumers, remove the duplicated Python dependency files:

- `requirements.txt`
- `requirements-dev.txt`
- `requirements-google.txt`

`requirements-rclone.txt` should not be converted into a uv dependency because rclone is an external executable, not a Python package. It can remain as an external-tool bootstrap/documentation file or be replaced by the managed project bootstrap (`uv run python main.py provider bootstrap`) and explicit installation documentation.

## Migration acceptance criteria

The complete migration should not be considered finished until all of the following are true:

- `uv.lock` is committed and reproducible.
- CI uses `uv sync --locked` and `uv run` for project operations.
- Linux, Windows and macOS remain covered for Python 3.11, 3.12 and 3.13.
- Google, TTS and packaging extras are exercised.
- `run_local`, scheduler and build scripts no longer depend on duplicated requirements files.
- PyInstaller builds continue to work on their supported platforms.
- CUDA runtime behavior is explicitly validated rather than mechanically rewritten.
- The clean wheel test still succeeds using pip.
- Documentation no longer presents requirements files as the primary installation path.
- A repository-wide search shows no accidental stale `pip install -r requirements*.txt` instructions.

This historical preview intentionally records the state before those production changes. PR #42 completed the infrastructure migration; `docs/UV_MIGRATION.md` is the current operational reference.