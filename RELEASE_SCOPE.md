# Release Scope — 1.4.0

## Current HEAD

- Branch baseline: `main`
- Current HEAD: `250fd2d239848c4f1f9b82485f602728b46cf71f`
- HEAD is the merge commit of PR #25 (`docs: establish repository governance and hygiene rules`).

## Previous release

- `v1.3.0`
- Commit: `620af6acbe3fca7d42ccd57f3585b3952cccf0a7`
- The tag is historical and must not be moved, deleted or reused.

## Changes since v1.3.0

Git reports 23 commits ahead of `v1.3.0`. The functional release scope is the post-1.3.0 regeneration feature plus repository governance/hygiene changes and release hardening required to make that state publishable.

| PR / change | Type | 1.4.0 | Evidence |
|---|---|---|---|
| PR #24 — explicit clean video regeneration | FEATURE | YES | `src/regeneration.py`, regeneration tests, new console entry point |
| PR #25 — repository governance and hygiene | GOVERNANCE / CI | YES | `CONTRIBUTING.md`, removal of one-off write workflow |
| Post-merge release hardening | FIX / TEST / CI / DOCUMENTATION / RELEASE | YES | This release branch; findings from integration audit |

The remaining commits between `v1.3.0` and current `main` are merge/topology commits and the implementation/documentation commits belonging to PR #24/#25; they are not independently reclassified as unrelated product features.

## Features entering 1.4.0

- Explicit `video-translation-regenerate` operation.
- Clean regeneration through the existing `MediaPipeline`.
- Backup/rollback semantics for existing registered outputs.
- Provider-specific local, Google Drive and rclone cleanup behavior.
- Repository governance and workflow hygiene from PR #25.

## Fixes entering 1.4.0

- Enforce the resource-manager concurrency ceiling after CLI overrides, so `--parallel-videos N` remains a request bounded by hardware-safe effective concurrency.
- Add explicit regression coverage for CLI concurrency clamping.
- Align release metadata and release documentation with the final candidate.

## Excluded changes

- No changes to `v1.3.0`.
- No unrelated historical commits are being cherry-picked or reinterpreted.
- No new audiovisual pipeline is introduced.
- No PyInstaller artefact is declared validated unless it is actually executed on a suitable runner.

## Known risks

- Google Drive and rclone regeneration are multi-operation workflows, not distributed transactions.
- Regeneration discovers existing outputs from manifests; unregistered orphan folders are intentionally not destroyed automatically.
- A release cannot be approved until the final candidate SHA has a fresh successful CI run covering all required jobs.
- Manual real-media validation remains distinct from mocked/unit validation.
