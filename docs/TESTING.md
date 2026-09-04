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
```

## Coverage areas

The repository contains tests for CLI recovery, extraction, FFmpeg resolution, naming, local storage, media identity/conversion, OAuth refresh, deduplication, path limits, performance/resource management, pipeline execution, provider runtime, resume, configuration, storage URIs/layout, STT, subtitle QA/repair, translation, quota handling, TTS and unattended readiness.

Naming tests cover both layers of the contract: inference of the logical ZIP/course/resource name and the final physical filesystem representation. Physical normalization is deliberately lossless for Unicode: inputs are canonicalized to NFC and accented characters such as `ñ` and `é` remain unchanged. Tests also cover separator normalization, punctuation/control handling, Windows reserved names, UTF-8 component limits and the `x` scope separator.

ZIP tests cover traversal, absolute/UNC Windows paths, reserved Windows components, nested archives, NFC canonicalization and case-folded Unicode collisions. These checks are security boundaries and must run on every supported platform.

External providers should be tested with deterministic mocks rather than requiring live network access. Model downloads and GPU execution are integration concerns and must not become requirements of the normal unit-test suite.
