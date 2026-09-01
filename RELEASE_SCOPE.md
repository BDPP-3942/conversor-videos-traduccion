# Release Scope — 1.4.1

## Previous release

`v1.4.0` → `ce1da6ea69a89f5a789c0670b200d6038f1a746d`.

The tag is historical and MUST NOT be moved, deleted, or reused.

## Changes since v1.4.0

The 1.4.1 corrective release is intentionally narrow. PR #29 already integrated the existing clean-regeneration operation into the local execution wrappers. The final release-validation PR aligns the release evidence with that implementation and adds direct subprocess coverage for the POSIX wrapper.

## Corrective scope

- `scripts/run_local.sh regenerate` dispatches to the existing `src.regeneration` implementation.
- `scripts/run_local.bat regenerate` dispatches to the same existing implementation on Windows.
- Regeneration continues to use the common `MediaPipeline` and public `StorageProvider` contract.
- Existing hardware-safe concurrency remains authoritative through `safe_parallelism()`; scripts do not duplicate it.
- Release E2E documentation and candidate evidence are aligned with the actual 1.4.1 code.

## Validation state

- `pyproject.toml` declares version `1.4.1`.
- README, CHANGELOG and release documentation identify `v1.4.0` as the previous published release and `1.4.1` as the corrective release.
- #27 and #28 are resolved and closed after their demonstrated validation.
- CI must validate the final release candidate on the exact final commit SHA.
- No `v1.4.1` tag exists until the release gate is satisfied.

## Excluded

- No changes to `v1.4.0`.
- No new media pipeline.
- No alternative storage or rollback implementation.
- No second concurrency algorithm.
- No unrelated product feature or broad refactor.
