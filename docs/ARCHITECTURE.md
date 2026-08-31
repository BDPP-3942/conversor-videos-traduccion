# Architecture

The application uses a common processing pipeline with replaceable storage and provider adapters. Video concurrency is resolved from the effective Whisper configuration and detected hardware before the pipeline creates workers.

```text
CLI / wrappers / executable / scheduler
                  │
                  ▼
          configuration loader
                  │
                  ▼
       Whisper/resource resolution
       CPU + RAM + optional GPU budget
                  │
                  ▼
       effective video parallelism
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
- `src/resource_profile.py`: hardware/resource detection, Whisper resolution and safe video concurrency.
- `src/subtitle_qa.py` and `src/subtitle_repair.py`: subtitle validation/repair.
- `src/translator.py` and `src/translation_providers.py`: translation orchestration and providers.
- `src/tts_pipeline.py`: cue-level synchronized TTS.
- `src/storage/`: storage abstraction and local/cloud implementations.
- `src/manifest.py`, `src/storage/processed_registry.py`: state and processed-result tracking.
- `src/output_deduplicator.py`: conservative duplicate analysis/deletion.
- `src/auth/`: Google OAuth, rclone management and unattended readiness checks.

## Resource-aware concurrency

The runtime resolves the effective Whisper device/model and estimates a conservative resource budget before calculating video concurrency. The calculation considers CPU threads, available RAM and GPU memory when CUDA is selected, while reserving headroom for the operating system, Python runtime and FFmpeg.

`max_parallel_videos = 0` means AUTO. Positive values are maximum requested concurrency and may be clamped to the safe hardware ceiling. A configured value of `1` remains a single worker.

This resource-aware concurrency behavior was introduced after the `1.2.2` release by PR #20. It is therefore part of the current `main` architecture, but not part of the published `1.2.2` release.

## Design constraints

1. Storage selection must not duplicate business logic.
2. VTT timing is the temporal contract between STT, translation and TTS.
3. Valid artifacts are reusable; invalid or missing artifacts are regenerated selectively.
4. Scheduled execution must not require interactive authentication.
5. Deletion operations must be conservative and revalidate their inputs.
6. Video concurrency must remain within a conservative resource budget rather than blindly saturating the host machine.
