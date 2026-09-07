# Release Candidate — 1.7.3

## Release

- **Version:** 1.7.3
- **Candidate SHA:** debe ser validado por CI y Release Gate sobre el SHA exacto final pre-merge; el tag debe apuntar al SHA exacto resultante de `main` tras el merge.
- **Previous release:** `v1.7.2` — release PATCH publicada con la corrección del gestor de descarga del modelo local.
- **Historical baselines:** `v1.7.1` → estado funcional inmediatamente anterior; `v1.7.0` → `036a9a4cf33012d0fcd0a784f8ff34db6e30b0f5`; `v1.6.0` → `a6cf0ee183a4802814fe0e061b4704e427166b85`; `v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.
- **Target tag:** `v1.7.3` — pending validation and publication.

This report is the release-gate record for the local translation model metadata bootstrap fix. The review baseline is the published `1.7.2` product state already integrated in `main`.

## Baseline for the 1.7.3 review

The comparison baseline is the merged and published `1.7.2` state. The review must preserve the STT selective-recovery fix, the `1.7.2` download-limit correction and all functionality consolidated through `1.7.0`.

## Scope

- Bundle the exact `config.json` and `tokenizer_config.json` required by the pinned local translation model.
- Install those bundled metadata files into the managed model directory before runtime validation.
- Keep `shared_vocabulary.json` as a downloaded and validated model artifact instead of duplicating its larger payload in the Python package.
- Add regressions proving the bundled metadata is available and that the complete prepared model still crosses the provider initialization and translation boundary.
- Keep the model repository and revision pinned.

## Root cause

The `1.7.2` downloader correctly recognized the JSON metadata as required model resources, but it still relied on a separate Hugging Face download for every JSON file. The actual runtime requires those metadata files to be present alongside `model.bin` before CTranslate2 can open the model. The small, revision-pinned `config.json` and `tokenizer_config.json` are now shipped with the application package and copied into the managed model directory during preparation.

`shared_vocabulary.json` remains a model artifact downloaded from the pinned Hugging Face revision and validated by the existing size/JSON checks.

## Dependencies

The runtime dependency contract remains unchanged:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`

## Tests

Required validation includes the complete pytest suite, local-translation download/provider regressions, STT regressions, configuration/provider regressions, reprocessing/manifests regressions, Unicode/filesystem and ZIP security tests, packaging validation and dependency audits.

The local-translation regressions verify that the bundled JSON metadata is installed, that `shared_vocabulary.json` remains downloaded, and that the prepared model can cross provider initialization and translation-call boundaries.

The real `scripts/benchmark_local_translation.py` remains the authoritative smoke test for the actual pinned model on the target machine.

## CI

CI validates the exact PR head on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13, plus project-wide Ruff lint/security/format checks, compile checks, dependency audits, packaging, clean-wheel installation, `pip check` and entry points.

## Packaging

`pyproject.toml` and `config/app.toml` declare `1.7.3`. The `config.local_translation_model` package data must be included in built distributions.

## Documentation

The release documentation for `1.7.3` is maintained in `CHANGELOG.md`, `docs/RELEASES.md`, `RELEASE_SCOPE.md`, this report and the local-translation/installation documentation. Historical release entries must remain intact.

## Known limitations

- CI uses deterministic test doubles for the model runtime and does not download the 78.7 MiB model on every runner.
- The real pinned model must be downloaded and benchmarked on the target macOS environment to validate the actual CTranslate2 + SentencePiece runtime.
- Real GPU benchmark performance remains hardware-dependent.

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality from `1.7.2` baseline | **PENDING final CI** |
| Bundled model metadata | **IMPLEMENTED** |
| Local provider runtime regression | **IMPLEMENTED** |
| Tests | **PENDING final CI** |
| CI | **PENDING** |
| Packaging | **PENDING final CI** |
| Documentation | **UPDATED** |
| Versioning | **UPDATED to 1.7.3** |

## Decision

**Do not merge or create `v1.7.3` until the final candidate SHA remains green in CI and Release Gate.** After merge, validate the resulting `main` SHA and create the immutable `v1.7.3` tag/release on that exact SHA.
