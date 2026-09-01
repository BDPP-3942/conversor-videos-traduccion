# Release Scope — 1.4.0

## Previous release

`v1.3.0` → `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`.

The tag is historical and MUST NOT be moved, deleted, or reused.

## Changes since v1.3.0

The 1.4.0 release candidate is the coherent set of changes represented by PR #24, PR #25 and PR #26, including the hardening required by #27 and #28.

## Features entering 1.4.0

- Explicit clean regeneration from the original source through the common `MediaPipeline`.
- Backup-before-regeneration and rollback-on-failure semantics where the storage backend supports the required operations.
- `video-translation-regenerate` package entry point.
- Repository governance and release hygiene.

## Fixes / hardening entering 1.4.0

- Safe concurrency enforcement for CLI overrides.
- Regeneration safety and provider consistency.
- Security/static-analysis quality.
- Reproducible packaging and documentation/version convergence.

## Validation state

- `pyproject.toml` declares version `1.4.0`.
- README and release/versioning documentation identify `1.3.0` as the previous published release and `1.4.0` as the current candidate.
- #27 and #28 are resolved and closed after validation.
- CI has validated the candidate branch head with the complete configured release checks.
- No `v1.4.0` tag exists until the release gate is satisfied.

## Excluded

- No changes to `v1.3.0`.
- No retroactive reinterpretation of historical releases.
- No speculative architecture rewrite.
- No unrelated product feature.
