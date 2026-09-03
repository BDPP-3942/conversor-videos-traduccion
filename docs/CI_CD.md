# CI/CD

GitHub Actions runs on pushes to `main` and release branches, and on pull requests targeting `main`.

The workflow is deliberately not triggered by every push to `feat/**` or `fix/**`: pull-request events already validate the submitted head SHA, and duplicate push-triggered matrices would consume private-repository Actions minutes without adding independent evidence.

## CI jobs

The CI is split by the type of evidence each check provides. Static/project-wide checks are not repeated for every operating system and Python version; platform compatibility tests are the only checks kept as a 3 × 3 runtime matrix.

### `quality`

Runs once on the self-hosted Linux runner (WSL2 Ubuntu) with Python 3.13. It checks:

- dependency consistency (`pip check`);
- Ruff imports/unused imports, lint, security and formatting;
- Python bytecode compilation.

These checks are not materially improved by running them nine times. Ruff analyzes the source tree, and `compileall`/`pip check` are project/environment checks rather than OS compatibility tests.

### `windows-test`

Runs on the self-hosted Windows runner with Python 3.11, 3.12 and 3.13. It checks:

- the complete pytest suite except the wheel-only packaging test;
- installed console entry points;
- the Windows `.bat` wrapper through PowerShell/CMD.

The three Python versions remain important because the package declares `>=3.11,<3.14`; dependency support and Python runtime behavior can differ between supported interpreter versions.

### `linux-test`

Runs on the self-hosted WSL2 Ubuntu runner with Python 3.11, 3.12 and 3.13. It checks:

- the complete pytest suite except the wheel-only packaging test;
- installed console entry points;
- POSIX shell syntax for the `.sh` wrappers.

This validates Linux/POSIX behavior separately from Windows behavior while keeping the supported Python-version matrix.

### `macos-test`

Runs on `macos-latest`, using GitHub-hosted macOS runners. macOS is intentionally not replaced by Windows or WSL2: those environments cannot provide equivalent macOS filesystem, process, executable and toolchain semantics.

If the repository has no available GitHub Actions budget, these macOS jobs cannot be replaced by the Windows/WSL self-hosted runners without weakening the meaning of the compatibility result. They should therefore be treated as **missing macOS evidence**, not as a successful substitute.

### `packaging`

Builds distributions, installs the wheel into a clean virtual environment, runs `pip check` and verifies the installed console entry points. It runs once on the self-hosted Linux runner because packaging behavior here is not an OS/Python compatibility matrix.

### `dependency-audit`

Installs the project with CI/cloud dependencies and runs `pip-audit --strict` against the dependency graph. It runs once on the self-hosted Linux runner.

### `tts-dependency-audit`

Audits the optional `[tts]` dependency graph separately with `pip-audit --strict`. It runs once on the self-hosted Linux runner.

## Self-hosted runner topology

The private development machine is expected to provide two GitHub Actions runners:

```text
Windows host
  labels: self-hosted, windows, x64
  purpose: Windows compatibility matrix

WSL2 Ubuntu
  labels: self-hosted, linux, x64
  purpose: Linux compatibility + quality + packaging + audits

GitHub-hosted
  macos-latest
  purpose: macOS compatibility matrix
```

One physical Windows machine can host the Windows runner and a separate Linux runner inside WSL2. The runners share the machine's CPU/RAM, so the Linux and Windows jobs should not be treated as independent physical machines. If only one runner exists for a given label set, matrix jobs queue rather than executing concurrently.

The self-hosted runners must be installed and online before the corresponding jobs can execute. If a matching self-hosted runner is offline, GitHub Actions queues the job rather than silently switching to another operating system.

## Why Python 3.11/3.12/3.13 remains a matrix

The project explicitly supports Python `>=3.11,<3.14`. Testing all three interpreters can expose differences in the Python runtime or in dependency compatibility. The matrix is therefore retained for `pytest` and platform-specific wrapper checks.

It is deliberately **not** retained for Ruff, formatting, compilation, packaging or dependency audits where repeating the same operation adds cost without proportional compatibility evidence.

## Local parity without Actions minutes

Before pushing, the same checks can be run directly on the development machine:

```bash
pytest
ruff check .
ruff check . --select S
ruff format --check .
python -m compileall config src main.py process_raw_videos.py process_videos.py
python -m pip check
python -m build
```

For stronger parity, run the test suite under Python 3.11, 3.12 and 3.13 on both Windows and WSL2. On Windows, also exercise the `.bat` wrapper; on WSL2, validate the `.sh` wrappers with Bash.

These local checks provide meaningful Windows/Linux evidence when GitHub Actions budget is unavailable, but they do not constitute macOS validation.

## macOS evidence policy when Actions budget is exhausted

The inability to run macOS is a **coverage gap**, not evidence that the code is broken. Its severity depends on how much the project relies on OS-specific behavior:

- **Low impact:** pure Python logic, configuration parsing, data transformation and tests that do not spawn platform-specific processes/filesystem operations.
- **Medium impact:** subprocesses, executable discovery, temporary files, path handling, environment variables, permissions and CLI behavior.
- **Higher impact:** native binaries, FFmpeg invocation, multiprocessing/process semantics, executable packaging, shell wrappers or dependencies with platform-specific wheels.

For this repository the impact is not negligible because the tests and application invoke subprocesses and FFmpeg, and the project contains both Windows and POSIX launcher scripts. The Windows + WSL2 split covers most of that surface, but it cannot prove macOS behavior.

Therefore, when no Actions budget is available, the recommended release evidence is:

1. Windows 3.11/3.12/3.13 self-hosted tests pass.
2. WSL2 Linux 3.11/3.12/3.13 self-hosted tests pass.
3. Quality, packaging and dependency audits pass on self-hosted Linux.
4. The release is explicitly marked **macOS validation pending** rather than claiming full 3-OS CI coverage.
5. Before a release that materially changes subprocess, filesystem, FFmpeg, packaging or shell behavior, reserve enough GitHub Actions budget to run the macOS matrix.

## Release Gate

`release-gate.yml` validates the exact candidate SHA, release metadata, distributions, packaged resources, clean wheel installation and source compilation. It is separate from the full compatibility matrix and does not replace it.

The Release Gate remains GitHub-hosted so release evidence retains a clean, disposable runner. If the GitHub Actions budget is exhausted, the release gate cannot provide its normal GitHub-hosted evidence and a release should not be presented as having completed the full release process solely from self-hosted CI.

## Actions-minute policy

Private-repository Actions minutes are a finite validation resource. To avoid unnecessary consumption:

- never rerun a successful job merely to obtain a second identical result;
- do not trigger full push matrices for feature/fix branches when the PR event validates the same head SHA;
- rely on concurrency cancellation when a newer commit supersedes an older run;
- use focused local checks before pushing a correction;
- keep project-wide quality checks outside the OS/Python compatibility matrix;
- reserve GitHub-hosted macOS runs for commits where macOS evidence is required;
- rerun the complete hosted compatibility evidence only for the final SHA that needs release evidence.
