# Release Scope — 1.4.0

## Current HEAD

`250fd2d239848c4f1f9b82485f602728b46cf71f` — merge of PR #25 (repository governance).

## Previous release

`v1.3.0` → `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`.

The tag is historical and MUST NOT be moved, deleted, or reused.

## Changes since v1.3.0

The Git comparison reports 23 commits ahead of `v1.3.0`. The functional/product changes are dominated by:

- PR #24 — explicit clean video regeneration: FEATURE.
- PR #25 — repository governance and hygiene: GOVERNANCE/DOCUMENTATION.

The comparison also contains the corresponding merge ancestry and post-release integration commits; earlier PRs #20–#23 are already represented by the published v1.3.0 baseline.

## Features entering 1.4.0

- Explicit clean regeneration from the original source through the common `MediaPipeline`.
- Backup-before-regeneration and rollback-on-failure semantics where the storage backend supports rename.
- `video-translation-regenerate` package entry point.
- Repository governance rules and removal of the one-off formatting workflow.

## Fixes / hardening entering 1.4.0

The release work will add or correct only issues demonstrated by the current code audit, with emphasis on:

- safe concurrency enforcement for CLI overrides;
- regeneration safety and provider consistency;
- security/static-analysis quality;
- reproducible packaging and documentation/version convergence.

## Excluded

- No changes to `v1.3.0`.
- No retroactive reinterpretation of historical releases.
- No speculative architecture rewrite.
- No unrelated new product feature.

## Known risks at audit start

- `pyproject.toml` still declares `1.3.0` while the target release is 1.4.0.
- README and release documentation still describe 1.3.0 as development/current rather than published.
- `docs/VERSIONING.md` contains obsolete reconstruction-era 5.x language.
- CLI `--parallel-videos` currently clamps only to at least one and can overwrite the resource-safe value.
- `MediaPipeline._effective_parallelism()` currently trusts the configured value for local execution instead of recalculating the hardware ceiling.
- The regeneration implementation monkey-patches private pipeline/storage members and contains provider-specific destructive operations outside the public storage contract; this requires explicit architectural review.
- There is no Actions run yet for this release-candidate branch; the latest main CI run validates SHA `250fd2d...`, not this candidate SHA.
