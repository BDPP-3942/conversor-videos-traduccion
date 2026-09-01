# Release Candidate — 1.4.0

## Release

- **Version:** 1.4.0
- **Candidate SHA:** recorded by the final Release Gate and release tag.
- **Previous release:** `v1.3.0` → `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`
- **Target tag:** `v1.4.0` — not created

This report describes the final 1.4.0 candidate. The exact release SHA is the commit selected by the Release Gate; the tag must point to that same immutable commit.

## Scope

- PR #26: release 1.4.0 integration, hardening and release-gate work.
- PRs included: #24, #25 and the hardening changes required by #27 and #28.
- PRs excluded: no unrelated product work is included in the release candidate.
- `v1.3.0` remains immutable.

## #27 — Safe parallelism

Resolved and closed after validation.

- `0` → AUTO.
- `1` → exactly one worker.
- `N > 1` → clamped to the hardware-safe limit.
- The CLI regression covers `--parallel-videos 999` through a real subprocess.

## #28 — Regeneration architecture

Resolved and closed after validation.

Regeneration uses the common `MediaPipeline` with `force_reprocess=True` and the public `StorageProvider` contract for backup, restore and cleanup. No monkey-patching of private pipeline/storage members remains in regeneration.

## Functionality

- Existing derived output is backed up before clean regeneration.
- Successful regeneration removes the obsolete backup.
- Failed regeneration restores the previous output and manifest where the provider supports the required operations.
- Source input is preserved.
- Existing resume, idempotency and duplicate handling remain in the common pipeline.

## E2E

The release suite uses real subprocess entry points with controlled local infrastructure, deterministic STT/translation adapters, real `MediaPipeline`, local storage and ffmpeg. It covers normal processing, dry-run, safe concurrency, resume, invalid resume artifacts, regeneration success, regeneration rollback, scheduled execution, duplicate handling, partial translation and cleanup.

The package does not declare a standalone `video-translation-scheduled` console entry point. Scheduled execution is `video-translation-pipeline run --scheduled`.

## Security

- Ruff Security is mandatory in CI.
- Dependency auditing covers normal and optional TTS dependency graphs.
- No formatter auto-commit or self-modifying workflow is used.
- Regeneration does not access provider private fields or private pipeline methods.
- Provider-specific destructive operations remain inside provider adapters.

## Tests

The final validated CI run passed the full configured pytest suite, including release E2E and provider-contract tests.

## CI

CI validates Python 3.11, 3.12 and 3.13, pytest, entry points, Ruff, Ruff Security, Ruff format, repository-wide compileall, pip check, pip-audit, distribution build and clean-wheel validation. The final candidate must have all jobs successful on the same SHA.

## Packaging

`pyproject.toml` declares `1.4.0`. Supported packaged entry points:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

`video-translation-scheduled` is not a declared console entry point.

## Documentation

README, CLI, regeneration, E2E, release and versioning documentation describe the 1.4.0 candidate and preserve the historical `v1.3.0` reference.

## Known limitations

- Google Drive and rclone are validated through deterministic provider contracts rather than real production credentials in CI.
- Full external TTS model/provider execution is not a mandatory networked CI dependency.

## Release Gate

| Gate | Status |
|---|---|
| Architecture | **PASS** |
| Functionality | **PASS** |
| E2E | **PASS** |
| Security | **PASS** |
| Tests | **PASS** |
| CI | **PASS** |
| Packaging | **PASS** |
| Documentation | **PASS** |
| Versioning | **PASS** |

## Decision

**APPROVE** — the candidate is ready to merge without additional release-specific changes. Create `v1.4.0` only from the final merged commit selected by the release process; do not modify that commit after validation.