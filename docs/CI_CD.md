# CI/CD

GitHub Actions runs on pushes to `main` and release branches, and on pull requests targeting `main`.

The workflow is deliberately not triggered by every push to `feat/**` or `fix/**`: pull-request events validate the submitted head SHA, while concurrency cancellation prevents obsolete runs from consuming resources.

## CI jobs

The CI is split by the type of evidence each check provides. Project-wide checks run once; platform compatibility checks are the only jobs kept as the 3 × 3 operating-system/interpreter matrix.

### `quality`

Runs once on `ubuntu-latest` with Python 3.13. It checks:

- dependency consistency (`pip check`);
- Ruff imports/unused imports, lint, security and formatting;
- Python bytecode compilation.

These checks are not materially improved by running them nine times. They validate the source tree or the project environment rather than OS-specific behavior.

### `windows-test`

Runs on `windows-latest` with Python 3.11, 3.12 and 3.13. It checks the complete test suite except the wheel-only packaging test, installed entry points and the Windows `.bat` wrapper.

### `linux-test`

Runs on `ubuntu-latest` with Python 3.11, 3.12 and 3.13. It checks the complete test suite except the wheel-only packaging test, installed entry points and POSIX shell syntax for the `.sh` wrappers.

### `macos-test`

Runs on `macos-latest` with Python 3.11, 3.12 and 3.13. It checks the complete test suite except the wheel-only packaging test, installed entry points and POSIX shell syntax.

macOS remains a real hosted target because Windows/Linux cannot prove macOS filesystem, process, native-library and path-normalization behavior.

### `packaging`

Builds distributions, installs the wheel into a clean virtual environment, runs `pip check` and verifies the installed console entry points. It runs once because this is packaging evidence, not OS compatibility evidence.

### `dependency-audit`

Installs the project with CI/cloud dependencies and runs `pip-audit --strict` against the dependency graph once.

### `tts-dependency-audit`

Audits the optional `[tts]` dependency graph separately with `pip-audit --strict` once.

## Why the checks are separated

The separation is about responsibility, not runner type:

- **Quality** owns static/project-wide validation.
- **Windows/Linux/macOS tests** own runtime and platform compatibility.
- **Packaging** owns distribution and clean-wheel validation.
- **Dependency audits** own dependency security validation.
- **Release Gate** owns release metadata and exact-candidate invariants.

A platform matrix must not repeat project-wide checks simply because it has multiple OS/Python combinations. Conversely, platform-specific behavior must not be reduced to a single Linux check.

## Exact SHA policy

PR jobs explicitly check out `github.event.pull_request.head.sha`. Therefore, evidence from an older SHA is not evidence for the current PR state. After a correction, the complete relevant workflow must finish again for the new final SHA.

## Release Gate

`release-gate.yml` validates the exact candidate SHA, release metadata, distributions, packaged resources, clean wheel installation and source compilation. On normal pull requests it validates release consistency without requiring the next version tag to be absent; the explicit manual release invocation additionally checks that the candidate tag does not already exist.

## Resource policy

The workflow uses concurrency cancellation so a newer commit supersedes an obsolete run. Do not rerun successful jobs merely to obtain duplicate evidence. Focused local checks are encouraged before pushing; the final SHA must receive the authoritative CI/Release Gate evidence before release approval.

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

For platform-specific confidence, run the test suite under Python 3.11, 3.12 and 3.13 on Windows, Linux/WSL2 and macOS when available. Windows should also exercise the `.bat` wrapper; POSIX systems should validate the `.sh` wrappers.

The CI workflow is authoritative for the exact commands and matrix.
