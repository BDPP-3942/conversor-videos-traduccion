# Release Candidate — 1.7.2

## Release

- **Version:** 1.7.2
- **Candidate SHA:** debe ser validado por CI y Release Gate sobre el SHA exacto final pre-merge; el tag debe apuntar al SHA exacto resultante de `main` tras el merge.
- **Previous release:** `v1.7.1` — estado funcional inmediatamente anterior, correspondiente al merge de la corrección STT ya integrada en `main`.
- **Historical baselines:** `v1.7.0` → `036a9a4cf33012d0fcd0a784f8ff34db6e30b0f5`; `v1.6.0` → `a6cf0ee183a4802814fe0e061b4704e427166b85`; `v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.
- **Target tag:** `v1.7.2` — not created

This report is the release-gate record for the local translation model download fix. The review baseline is the complete `1.7.1` product state already integrated in `main`.

## Baseline for the 1.7.2 review

The comparison baseline is the merged `1.7.1` state. The review must preserve the STT selective-recovery fix and all functionality consolidated through `1.7.0`, including reprocessing/manifests, deterministic Unicode naming/filesystem behavior and the local-translation runtime.

## Scope

- Corregir el cálculo del límite de descarga de los ficheros del modelo local.
- Evitar la evaluación eager del fallback de `dict.get`, que provoca `KeyError: 'model.bin'` al descargar un fichero principal presente en `MODEL_FILES`.
- Mantener descarga pública sin autenticación y token opcional para entornos que lo requieran.
- Mantener validación por tamaño, SHA-256 y estructura de metadatos.
- Añadir regresión que ejercita todos los ficheros gestionados durante la descarga.
- Añadir regresión que inicializa el proveedor con el modelo preparado y ejecuta una traducción.

## Root cause

El código calculaba el límite con `MODEL_FILES.get(name, (0, SMALL_MODEL_FILES[name][0]))[1]`. En Python, el argumento por defecto de `dict.get` se evalúa antes de llamar al método. Por ello, incluso cuando `name` era `model.bin` y sí existía en `MODEL_FILES`, se evaluaba `SMALL_MODEL_FILES[name][0]` y se producía `KeyError: 'model.bin'`.

La corrección selecciona el límite mediante una rama explícita entre `MODEL_FILES` y `SMALL_MODEL_FILES`, evitando evaluar una estructura que no corresponde al fichero actual.

## Dependencies

The runtime dependency contract remains unchanged:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`

## Tests

Required validation includes the complete pytest suite, local-translation download/provider regressions, STT regressions, configuration/provider regressions, reprocessing/manifests regressions, Unicode/filesystem and ZIP security tests, packaging validation and dependency audits.

The local-translation regressions verify that all model files are downloaded and validated, and that the prepared model can cross the provider initialization and translation-call boundary. The real `scripts/benchmark_local_translation.py` remains the authoritative smoke test for the actual pinned model on the target machine.

## CI

CI validates the exact PR head on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13, plus project-wide Ruff lint/security/format checks, compile checks, dependency audits, packaging, clean-wheel installation, `pip check` and entry points.

## Packaging

`pyproject.toml` declares `1.7.2`.

## Documentation

The release documentation for `1.7.2` is maintained in `CHANGELOG.md`, `docs/RELEASES.md`, `RELEASE_SCOPE.md`, this report and the local-translation/installation documentation. Historical release entries must remain intact.

## Known limitations

- CI uses deterministic test doubles for the model runtime and does not download the 78.7 MiB model on every runner.
- The real pinned model must be downloaded and benchmarked on the target macOS environment to validate the actual CTranslate2 + SentencePiece runtime.
- Real GPU benchmark performance remains hardware-dependent.

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality from `1.7.1` baseline | **PENDING final CI** |
| Local model download regression | **IMPLEMENTED** |
| Local provider runtime regression | **IMPLEMENTED** |
| Tests | **PENDING final CI** |
| CI | **PENDING** |
| Packaging | **PENDING final CI** |
| Documentation | **UPDATED** |
| Versioning | **UPDATED to 1.7.2** |

## Decision

**Do not merge or create `v1.7.2` until the final candidate SHA remains green in CI and Release Gate.** After merge, validate the resulting `main` SHA and create the immutable `v1.7.2` tag/release on that exact SHA.
