# CI/CD

GitHub Actions runs on pushes to `main` and pull requests targeting `main`.

## CI jobs

### `test`

Runs the test and quality matrix on Python 3.11, 3.12 and 3.13. It checks dependency consistency, pytest, installed entry points, Ruff imports/lint/security/formatting and Python compilation.

### `packaging`

Builds distributions, installs the wheel into a clean virtual environment, runs `pip check` and verifies the installed console entry points.

### `dependency-audit`

Installs the project with CI/cloud dependencies and runs `pip-audit --strict` against the dependency graph.

### `tts-dependency-audit`

Audits the optional `[tts]` dependency graph separately with `pip-audit --strict`.

## Local parity

At minimum, run:

```bash
pytest
ruff check .
ruff format --check .
python -m compileall config src main.py process_raw_videos.py process_videos.py
```

The CI workflow is authoritative for the exact job matrix and commands.
