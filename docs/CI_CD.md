# CI/CD

GitHub Actions runs on pushes to `main` and release branches, and on pull requests targeting `main`.

The workflow is deliberately not triggered by every push to `feat/**` or `fix/**`: pull-request events already validate the submitted head SHA, and duplicate push-triggered matrices would consume private-repository Actions minutes without adding independent evidence.

## CI jobs

### `test`

Runs the test and quality matrix on Python 3.11, 3.12 and 3.13 across Linux, Windows and macOS. It checks dependency consistency, pytest, installed entry points, Ruff imports/lint/security/formatting and Python compilation.

The pull-request workflow explicitly checks out `github.event.pull_request.head.sha`. Therefore, the latest run for the latest submitted PR SHA is the source of truth for PR validation; results from older SHAs are not evidence for the current PR state.

The matrix uses `fail-fast` so a known failing SHA does not continue consuming all remaining matrix minutes. Once the failure is corrected, the final SHA is run again and must pass the complete matrix before approval.

### `packaging`

Builds distributions, installs the wheel into a clean virtual environment, runs `pip check` and verifies the installed console entry points.

### `dependency-audit`

Installs the project with CI/cloud dependencies and runs `pip-audit --strict` against the dependency graph.

### `tts-dependency-audit`

Audits the optional `[tts]` dependency graph separately with `pip-audit --strict`.

## Release Gate

`release-gate.yml` validates the exact candidate SHA, release metadata, distributions, packaged resources, clean wheel installation and source compilation. It is separate from the full CI matrix and does not replace it.

## Actions-minute policy

Private-repository Actions minutes are a finite validation resource. To avoid unnecessary consumption:

- never rerun a successful job merely to obtain a second identical result;
- do not trigger full push matrices for feature/fix branches when the PR event validates the same head SHA;
- rely on concurrency cancellation when a newer commit supersedes an older run;
- use focused local checks before pushing a correction;
- rerun the full matrix only for the final SHA that needs release evidence.

## Local parity

At minimum, run:

```bash
pytest
ruff check .
ruff check . --select S
ruff format --check .
python -m compileall config src main.py process_raw_videos.py process_videos.py
python -m pip check
python -m build
```

The CI workflow is authoritative for the exact job matrix and commands.
