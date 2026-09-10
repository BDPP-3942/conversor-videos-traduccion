# Release Candidate — 1.7.4

## Release

- **Version:** 1.7.4
- **Candidate SHA:** debe ser validado por CI y Release Gate sobre el SHA exacto final pre-merge; el tag debe apuntar al SHA exacto resultante de `main` tras el merge.
- **Previous release:** `v1.7.2` — release PATCH publicada con la corrección del gestor de descarga del modelo local.
- **Historical baselines:** `v1.7.1` → corrección de recuperación STT; `v1.7.0` → `036a9a4cf33012d0fcd0a784f8ff34db6e30b0f5`; `v1.6.0` → `a6cf0ee183a4802814fe0e061b4704e427166b85`; `v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.
- **Target tag:** `v1.7.4` — pending validation and publication.

This report is the release-gate record for the maintenance release that consolidates local-translation validation fixes and the complete migration of development, CI, packaging and dependency auditing to `uv`.

## Baseline for the 1.7.4 review

The comparison baseline is the published `1.7.2` product state. The review preserves the STT selective-recovery fix and the local-translation fixes already integrated after that baseline.

## Scope

- Accept the real JSON-root shape of `shared_vocabulary.json`.
- Preserve the packaged `config.json` and `tokenizer_config.json` metadata required by the pinned local translation model.
- Make `pyproject.toml` the single dependency declaration source.
- Commit `uv.lock` as the reproducible dependency resolution.
- Run development, test, build and audit environments through locked uv environments.
- Keep pip as the clean-wheel compatibility mechanism for published distributions.

## CI / dependency audit

CI uses `uv sync --locked` for project environments and `uv pip check` for dependency consistency. The audit tooling is declared in the `audit` dependency group and invoked with `uv run --locked --group audit pip-audit --strict`; no global `pip-audit` installation is assumed.

The test matrix remains Linux, Windows and macOS with Python 3.11, 3.12 and 3.13. Packaging still verifies a wheel in an isolated pip environment.

## Tests

Required validation includes the complete pytest suite, local-translation regressions, STT regressions, configuration/provider regressions, reprocessing/manifests regressions, Unicode/filesystem and ZIP security tests, packaging validation, dependency consistency and dependency audits.

## Documentation

The release documentation for `1.7.4` is maintained in `CHANGELOG.md`, `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_SCOPE.md`, this report and the CI/development documentation. Historical release entries must remain intact.

## Known limitations

- CI uses deterministic test doubles for the local model runtime and does not download the full production model on every runner.
- Real model benchmark performance remains hardware-dependent.
- The uv migration does not remove pip from the published-wheel compatibility path or from portable CUDA runtime fallbacks.

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality from `1.7.2` baseline | **PENDING final CI** |
| Local translation validation | **IMPLEMENTED** |
| uv dependency resolution | **IMPLEMENTED** |
| Locked CI environments | **IMPLEMENTED** |
| Tests | **PENDING final CI** |
| CI | **PENDING** |
| Packaging | **PENDING final CI** |
| Documentation | **UPDATED** |
| Versioning | **UPDATED to 1.7.4** |

## Decision

**Do not merge or create `v1.7.4` until the final candidate SHA remains green in CI and Release Gate.** After merge, validate the resulting `main` SHA and create the immutable `v1.7.4` tag/release on that exact SHA.
