# Testing

The test suite is configured through `pyproject.toml` and lives under `tests/`.

## Local checks

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

For a focused test run:

```bash
pytest tests/test_pipeline.py
pytest tests/test_tts_pipeline.py
pytest tests/test_reprocessor.py
```

## Coverage areas

The repository contains tests for CLI recovery, extraction, FFmpeg resolution, naming, local storage, media identity/conversion, OAuth refresh, deduplication, path limits, performance/resource management, pipeline execution, provider runtime, resume, configuration, storage URIs/layout, STT, subtitle QA/repair, translation, quota handling, TTS and unattended readiness.

External providers should be tested with deterministic mocks rather than requiring live network access.
