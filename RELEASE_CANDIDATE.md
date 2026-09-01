# Release Candidate — 1.4.1

## Release

- **Version:** 1.4.1
- **Candidate SHA:** `658dea2e0b94f5e164e5b148f67d81b843f2094c` (baseline; final SHA must be this report's final commit)
- **Previous release:** `v1.4.0` → `ce1da6ea69a89f5a789c0670b200d6038f1a746d`
- **Target tag:** `v1.4.1` — not created

This report is the release-gate record for the corrective patch. The tag must point to the exact final validated commit and must never be moved afterward.

## Scope

- Corrective integration of the existing clean-regeneration operation into the existing local execution wrappers.
- No new media pipeline, storage implementation, rollback implementation or concurrency algorithm.
- `v1.4.0` remains immutable.

## PRs included

- PR #29 — merged into `main`; introduced the corrective wrapper integration and version/documentation alignment.
- This final-validation PR — adds/updates only release-gate evidence and validation coverage required to prove the integrated wrapper path.

## PRs excluded

- No unrelated feature or refactor work.
- PR #26 is not reused as the release PR.

## #27 — Safe parallelism

Resolved and closed. The central `safe_parallelism()` implementation remains authoritative: `0` selects AUTO, `1` remains one worker, and positive values are clamped to the hardware-safe ceiling. CLI overrides do not implement a second concurrency algorithm.

## #28 — Regeneration architecture

Resolved and closed. `src.regeneration` uses the common `MediaPipeline` with `force_reprocess=True` and the public `StorageProvider` backup/restore/delete contract. No regeneration path relies on private pipeline/storage members.

## Existing functionality reused

- `src.regeneration.main()` / `video-translation-regenerate`.
- Common `MediaPipeline`.
- Public `StorageProvider` regeneration contract.
- Existing `safe_parallelism()` implementation.
- Existing local, cloud and rclone provider adapters.

## Scripts modified

- `scripts/run_local.sh` — dispatches `regenerate` to `python -m src.regeneration`.
- `scripts/run_local.bat` — dispatches `regenerate` to the same existing module.

No script contains regeneration, storage, rollback or concurrency business logic.

## Architecture

`run_local wrapper → src.regeneration → MediaPipeline → StorageProvider → provider adapter`.

The wrapper is an execution/orchestration layer only.

## Functionality

- Normal processing remains on the existing pipeline.
- Clean regeneration backs up existing outputs, regenerates through the common pipeline, removes backups only after success and restores them on failure where the provider contract supports it.
- Source input remains preserved.
- CLI concurrency remains hardware-safe.

## E2E

The release E2E suite uses real subprocess execution, temporary local storage, deterministic external adapters, real `MediaPipeline`, local storage and ffmpeg. Regeneration is exercised through the packaged entry point and the local POSIX wrapper where the test environment supports it.

The package does not declare a standalone `video-translation-scheduled` console entry point. Scheduled execution remains `video-translation-pipeline run --scheduled`.

## Security

- Ruff Security is mandatory.
- Dependency auditing covers normal and optional TTS graphs.
- No new shell command construction or `shell=True` was introduced by the corrective integration.
- The wrappers dispatch only to fixed local Python modules and forward argument lists.
- Regeneration remains isolated behind the public storage contract.

## Tests

Required validation includes the complete pytest suite, CLI concurrency regressions, regeneration contract/regression tests and real subprocess E2E. Wrapper execution is covered separately from the packaged regeneration entry point.

## CI

The configured CI matrix validates Python 3.11, 3.12 and 3.13, pytest, entry points, Ruff, Ruff Security, Ruff format, compileall, pip check, pip-audit, distribution build and clean-wheel validation.

## Packaging

`pyproject.toml` declares `1.4.1`. Supported packaged entry points:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

`video-translation-scheduled` is not declared and is therefore NOT APPLICABLE.

## Documentation

README, `docs/RELEASES.md`, `docs/UNATTENDED.md`, `CHANGELOG.md`, the E2E matrix and this report must describe the final 1.4.1 behavior without claiming unvalidated release state.

## Known limitations

- Google Drive and rclone production credentials are outside deterministic CI and are covered through public provider contracts.
- Full external TTS model/provider execution is not a mandatory networked CI dependency.
- Windows `.bat` execution cannot be exercised by the Linux GitHub runner and requires Windows validation if it is to be marked validated rather than NOT VALIDATED.

## Script validation matrix

| Caso de uso | Script | Entry point | Resultado esperado | Estado |
|---|---|---|---|---|
| Ejecución normal | `scripts/run_local.*` | `video-translation-pipeline` / `main.py run` | success | VALIDATE |
| Dry run | `scripts/run_local.*` | `main.py run --dry-run` | no processing side effects | VALIDATE |
| AUTO concurrency | `scripts/run_local.*` | `main.py run --parallel-videos 0` | safe effective concurrency | VALIDATE |
| Explicit concurrency | `scripts/run_local.*` | `main.py run --parallel-videos 1` | exactly 1 | VALIDATE |
| Excessive concurrency | `scripts/run_local.*` | `main.py run --parallel-videos 999` | clamped safely | VALIDATE |
| Resume | `scripts/run_local.*` | `main.py run` | reuse valid artifacts | VALIDATE |
| Invalid artifact | `scripts/run_local.*` | `main.py run` | reprocess invalid artifact | VALIDATE |
| Regeneration success | `scripts/run_local.sh` | `src.regeneration` | new result, backup removed | VALIDATE |
| Regeneration failure | `video-translation-regenerate` | `src.regeneration` | rollback | VALIDATE |
| TTS | existing TTS wrapper/entry point | `src.tts_cli` | correct output/help | VALIDATE |
| Scheduled | `scripts/run_scheduled.*` | `video-translation-pipeline run --scheduled` | common pipeline | VALIDATE |
| Standalone `video-translation-scheduled` | none | none | unsupported | NOT APPLICABLE |
| Local storage | existing scripts | `LocalStorageProvider` | success | VALIDATE |
| Storage failure | existing tests/scripts | provider contract | correct failure | VALIDATE |
| Remote storage contract | existing tests | provider adapters | correct public contract | VALIDATE |
| Duplicate | existing scripts | main pipeline | skip/reuse | VALIDATE |
| Partial translation | existing scripts | main pipeline | partial state | VALIDATE |
| Cleanup | existing scripts | common pipeline | no unsafe residue | VALIDATE |

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality | **PASS** |
| Script integration | **PASS** |
| Architecture | **PASS** |
| Functionality | **PASS** |
| E2E | **BLOCK** — final validation run required on the final SHA |
| Security | **BLOCK** — final validation run required on the final SHA |
| Tests | **BLOCK** — final validation run required on the final SHA |
| CI | **BLOCK** — final validation run required on the final SHA |
| Packaging | **BLOCK** — final build must correspond to final SHA |
| Documentation | **PASS** |
| Versioning | **PASS** |

## Decision

**BLOCK RELEASE** until the final commit has a complete local validation record and a green GitHub Actions run on that exact SHA. No `v1.4.1` tag is created by this report.
