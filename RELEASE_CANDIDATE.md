# Release Candidate — 1.4.0

## Release

- **Version:** 1.4.0
- **Candidate SHA at report creation:** `1bb709c82c648e6bb1c1fe1225eebf1bdb092ede`
- **Previous release:** `v1.3.0` → `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`
- **Target tag:** `v1.4.0` — not created

## Scope

The comparison `v1.3.0...main` contains 23 commits. The relevant post-release product evolution is:

| PR | Change | Type | 1.4.0 |
|---|---|---|---|
| #24 | Explicit clean video regeneration | FEATURE | YES |
| #25 | Repository governance and hygiene | GOVERNANCE / DOCUMENTATION | YES |

PRs #20–#23 form the already-published v1.3.0 baseline and are not reintroduced as new features. The v1.3.0 tag remains immutable.

## Features

- Clean regeneration from the original source through the common `MediaPipeline`.
- Backup before regeneration and rollback where storage rename permits it.
- `video-translation-regenerate` entry point.
- Governance rules and removal of the one-off format-writing workflow.

## Bug fixes / hardening

- Package metadata and release documentation are aligned to 1.4.0 on this candidate branch.
- The audit identified a concurrency override defect that is **not yet fixed**.
- The audit identified an architectural contract problem in regeneration that is **not yet fixed**.

## Security

The existing CI has a successful Ruff Security and dependency-audit run on the current `main` SHA. That result cannot approve this candidate because the candidate SHA has not received the required CI run yet.

Manual review found no evidence in the inspected regeneration implementation of `shell=True`; rclone execution uses an argv list and explicit subprocess timeout. However, regeneration currently reaches provider internals/private fields, so the architectural security/reliability boundary is not considered closed.

## Tests

The repository contains broad regression coverage, including resource management, resume, regeneration, storage, STT, subtitles, translation and TTS. The release audit has not yet demonstrated the mandatory new CLI regression for `--parallel-videos 999`.

## CI

Latest verified successful GitHub Actions run:

- SHA: `250fd2d239848c4f1f9b82485f602728b46cf71f`
- Workflow: CI
- Python: 3.11, 3.12, 3.13
- Packaging: success
- Dependency audit: success
- TTS dependency audit: success
- Ruff / Ruff Security / format / compileall: success

This is **not** the final candidate SHA. The candidate currently has no status checks recorded, so CI is not a release gate pass.

## Packaging

`pyproject.toml` now declares `1.4.0` on this branch. The package entry points include:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

Packaging was successful on the pre-candidate main SHA, including installation of the wheel and `--help` checks, but packaging must be rerun on the final candidate SHA.

PyInstaller artifacts have not been declared validated by this audit.

## Documentation

Updated on this candidate branch:

- `README.md`
- `CHANGELOG.md`
- `docs/RELEASES.md`
- `docs/VERSIONING.md`
- `RELEASE_SCOPE.md`
- `RELEASE_CANDIDATE.md`

`docs/REGENERATION.md` already documents the feature and its distributed-storage limitations. It should be reconciled with the final implementation after architectural hardening.

## Known limitations / blockers

### CRITICAL — concurrency contract violation

`main.py` applies `--parallel-videos` after resource tuning and converts zero to one. `src/pipeline.py::_effective_parallelism()` then returns the configured value for local storage. Consequently an explicit value such as `--parallel-videos 999` can bypass the hardware-safe ceiling. This contradicts the stated 0=AUTO / 1=single / N=bounded-by-safe-limit contract.

Tracked in issue #27.

### HIGH — regeneration contract leakage

`src/regeneration.py` monkey-patches private `MediaPipeline` methods/attributes and accesses private provider implementation details to perform destructive cleanup. The public `StorageProvider` contract does not expose a regeneration/delete operation. This makes the release behavior dependent on private implementation details.

Tracked in issue #28.

### RELEASE — candidate CI not validated

No status checks are recorded for the candidate SHA at report creation. A successful CI run on another SHA cannot be substituted.

## Release Gate

| Gate | Status |
|---|---|
| Architecture | **BLOCK** — regeneration contract leakage |
| Functionality | **BLOCK** — concurrency override can bypass safe ceiling |
| Security | **BLOCK** — boundary review not closed; candidate checks pending |
| Tests | **BLOCK** — mandatory CLI concurrency regression not yet demonstrated |
| CI | **BLOCK** — no checks on final candidate SHA |
| Packaging | **BLOCK** — 1.4.0 candidate build not yet rerun after final fixes |
| Documentation | PASS with condition — candidate docs aligned, regeneration docs need final implementation reconciliation |
| Versioning | PASS for candidate branch — `pyproject.toml` is 1.4.0; tag intentionally absent |

## Decision

**BLOCK RELEASE**

The repository is not yet publishable as `v1.4.0`.

The correct next steps are to fix #27, harden #28, add/execute the required regression suite, rerun all local and GitHub checks on the resulting final SHA, rebuild/package that exact SHA, reconcile documentation, and only then create `v1.4.0` on the validated commit.
