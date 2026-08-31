# Architecture

The application uses a common processing pipeline with replaceable storage and provider adapters.

```text
CLI / wrappers / executable / scheduler
                  │
                  ▼
          configuration loader
                  │
                  ▼
          common MediaPipeline
          ┌───────┼────────┐
          ▼       ▼        ▼
         STT   translation  TTS
          │       │        │
          └───────┼────────┘
                  ▼
        artifact validation
                  │
                  ▼
          storage adapter
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    local     Google Drive   rclone
```

## Main components

- `main.py`: CLI parsing, readiness checks, logging, runtime locking and orchestration.
- `config/`: TOML/environment configuration and path resolution.
- `src/pipeline.py`: common media-processing workflow.
- `src/stt_engine.py`: `faster-whisper` transcription.
- `src/subtitle_qa.py` and `src/subtitle_repair.py`: subtitle validation/repair.
- `src/translator.py` and `src/translation_providers.py`: translation orchestration and providers.
- `src/tts_pipeline.py`: cue-level synchronized TTS.
- `src/storage/`: storage abstraction and local/cloud implementations.
- `src/manifest.py`, `src/storage/processed_registry.py`: state and processed-result tracking.
- `src/output_deduplicator.py`: conservative duplicate analysis/deletion.
- `src/auth/`: Google OAuth, rclone management and unattended readiness checks.

## Design constraints

1. Storage selection must not duplicate business logic.
2. VTT timing is the temporal contract between STT, translation and TTS.
3. Valid artifacts are reusable; invalid or missing artifacts are regenerated selectively.
4. Scheduled execution must not require interactive authentication.
5. Deletion operations must be conservative and revalidate their inputs.
