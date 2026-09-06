# Testing

The test suite is configured through `pyproject.toml` and lives under `tests/`.

## Local checks

```bash
pytest
ruff check .
ruff check . --select S
ruff format --check .
python -m compileall .
```

For a focused test run:

```bash
pytest tests/test_pipeline.py
pytest tests/test_tts_pipeline.py
pytest tests/test_reprocessor.py
pytest tests/test_file_naming.py
pytest tests/test_naming_reference.py
pytest tests/test_extractor.py
pytest tests/test_local_translation.py
```

## Coverage areas

The repository contains tests for CLI recovery, extraction, FFmpeg resolution, naming, local storage, media identity/conversion, OAuth refresh, deduplication, path limits, performance/resource management, pipeline execution, provider runtime, resume, configuration, storage URIs/layout, STT, subtitle QA/repair, translation, quota handling, TTS and unattended readiness.

Naming tests cover both layers of the contract: inference of the logical ZIP/course/resource name and the final physical filesystem representation. Physical normalization follows NFD → remove combining diacritical marks → NFC and then lowercases/case-folds the physical representation; inputs such as `ñ` and `é` therefore become `n` and `e`. Tests also cover separator normalization, punctuation/control handling, Windows reserved names, UTF-8 component limits and the `x` scope separator.

ZIP tests cover traversal, absolute/UNC Windows paths, reserved Windows components, nested archives, NFC canonicalization and case-folded Unicode collisions. These checks are security boundaries and must run on every supported platform.

Local translation tests cover pinned-model validation, resumable downloads, optional Hugging Face authorization, CPU fallback when CUDA probing fails and the CTranslate2/SentencePiece batch-output contract. The normal unit-test suite uses mocks and does not require downloading the model or having a GPU.

The local translation benchmark is the hardware-level smoke test: `python scripts/benchmark_local_translation.py --sentences 100` must be run on the target machine after preparing the model. It verifies real model initialization and rejects empty translation output.

External providers should be tested with deterministic mocks rather than requiring live network access. Model downloads and GPU execution are integration concerns and must not become requirements of the normal unit-test suite.
