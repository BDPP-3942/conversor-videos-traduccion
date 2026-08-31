# Release Candidate — 1.4.0

## Release

- **Version:** 1.4.0
- **Candidate SHA at report creation:** `9dd44ee2477808ea9a9e0855a09c16a0df0eedd1`
- **Previous release:** `v1.3.0` → `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`
- **Target tag:** `v1.4.0` — not created

The report records the last code-validation SHA before this documentation-only reconciliation commit. A release tag must point to the final immutable commit selected by the Release Gate; the tracked report cannot contain that commit's own SHA without becoming self-referential.

## Scope

- PR #26: release 1.4.0 integration, hardening and release-gate work.
- PRs included: #24, #25 and the hardening changes required by #27 and #28.
- PRs excluded: no unrelated product work is included in the release candidate.
- `v1.3.0` remains immutable.

## #27 — Safe parallelism

Resolved in code and regression coverage.

The effective concurrency path is now:

```text
requested CLI value
        ↓
resolved AppSettings
        ↓
safe_parallelism()
        ↓
MediaPipeline._effective_parallelism()
        ↓
effective worker count
```

Contract:

- `0` → AUTO.
- `1` → exactly one worker.
- `N > 1` → clamped to the hardware-safe limit.

The CLI regression exercises `--parallel-videos 999` through a real subprocess and asserts that it cannot exceed the AUTO safe limit.

## #28 — Regeneration architecture

Resolved in code and contract coverage.

Regeneration now uses the common `MediaPipeline` with `force_reprocess=True` and only the public `StorageProvider` regeneration contract:

- `backup_output_folder()`
- `restore_output_backup()`
- `delete_output_backup()`

No monkey-patching of pipeline/storage internals is used by regeneration. Local, Google Drive and rclone providers expose the contract; remote behavior is covered with deterministic provider fakes.

## Functionality

- Clean regeneration backs up existing derived output before processing.
- Successful regeneration validates through the common pipeline and removes the backup.
- Failed regeneration restores the previous output and manifest state where the provider exposes the required operations.
- Source input is preserved by the regeneration operation.
- Existing resume/idempotency and duplicate handling remain in the common pipeline.

## E2E

The release E2E suite uses real subprocess entry points and controlled local infrastructure:

- temporary filesystem;
- deterministic STT/translation adapters only for external model/API boundaries;
- real `MediaPipeline`;
- real ffmpeg conversion;
- real local storage;
- real regeneration entry point;
- success and rollback scenarios;
- CLI dry-run, scheduled mode and concurrency regression.

The package does not currently declare a standalone `video-translation-scheduled` console entry point. Scheduled execution is `video-translation-pipeline run --scheduled` and is tested through that real entry point.

## Security

- Ruff Security is a mandatory CI job.
- Dependency auditing is mandatory for the normal and optional TTS dependency graphs.
- No new `noqa`, `continue-on-error`, formatter auto-commit or self-modifying workflow was introduced.
- Regeneration does not access provider private fields or private pipeline methods.
- Provider-specific destructive operations remain inside the provider adapter.

## Tests

Coverage is behavior-oriented rather than percentage-driven and includes unit, integration, subprocess E2E, regeneration rollback and provider-contract tests. The mandatory full suite remains a release gate and must pass on the final candidate SHA.

## CI

The CI workflow now runs on pushes to `release/1.4.0-hardening` so the branch-head SHA can be validated directly. Required validation includes Python 3.11/3.12/3.13, pytest, Ruff, Ruff Security, Ruff format, repository-wide compileall, pip check, pip-audit, distribution build and clean-wheel entry-point checks.

A successful run on another SHA is never substituted for the final candidate run.

## Packaging

`pyproject.toml` declares `1.4.0` and the packaged entry points are:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

`video-translation-scheduled` is not a declared entry point and is therefore not represented as a supported package executable.

## Documentation

The CLI, regeneration architecture and explicit E2E matrix were reconciled with the hardening implementation. The historical `v1.3.0` tag and release documentation remain unchanged.

## Known limitations

- Google Drive and rclone are not exercised against real remote accounts in CI; their public storage contract is validated with deterministic fakes. Real cloud credentials are intentionally excluded from CI.
- TTS is validated at the packaged entry-point level in the release suite; the full external TTS provider requires its optional runtime/model environment and is not a mandatory networked CI test.
- The report's own commit SHA cannot be truthfully embedded into its content because doing so changes the SHA. The exact final release SHA is therefore recorded by the Release Gate and tag, while this report records the preceding code-validation SHA.

## Release Gate

| Gate | Status |
|---|---|
| Architecture | **BLOCK** until final SHA validation |
| Functionality | **BLOCK** until final SHA validation |
| E2E | **BLOCK** until final SHA validation |
| Security | **BLOCK** until final SHA validation |
| Tests | **BLOCK** until final SHA validation |
| CI | **BLOCK** until final SHA validation |
| Packaging | **BLOCK** until final SHA validation |
| Documentation | **PASS** for reconciled documentation |
| Versioning | **PASS** for 1.4.0 metadata; tag intentionally absent |

## Decision

**BLOCK RELEASE** until every required gate is demonstrated on one final SHA. Issues #27 and #28 must remain open until the final validation is complete; they may only be closed after the behavior is demonstrated and the release gate is PASS.
