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
- `src/file_naming.py`: shared logical/physical filename normalization and filesystem-boundary enforcement.
- `src/naming_policy.py`: inference of course/lesson metadata and logical output stems.
- `src/archive_naming.py`: ZIP naming interpretation used by the naming policy.
- `src/subtitle_qa.py` and `src/subtitle_repair.py`: subtitle validation/repair.
- `src/translator.py` and `src/translation_providers.py`: translation orchestration and providers.
- `src/tts_pipeline.py`: cue-level synchronized TTS.
- `src/storage/`: storage abstraction and local/cloud implementations.
- `src/manifest.py`, `src/storage/processed_registry.py`: state and processed-result tracking.
- `src/output_deduplicator.py`: conservative duplicate analysis/deletion.
- `src/auth/`: Google OAuth, rclone management and unattended readiness checks.

## Naming and filesystem boundary

Naming has two explicit stages. `naming_policy` derives the logical course/resource identity from the ZIP and source context; `file_naming` then converts the resulting component into the physical filesystem representation. This prevents a logical name from bypassing the final platform-safety checks.

The physical contract is:

```text
<curso_o_contenedor>x<nombre_sanitizado>
```

`x` is the scope separator and `_` is the internal word separator. Physical normalization is deterministic: Unicode is first canonicalized to NFC and retained losslessly; whitespace and separator hyphens become `_`; incompatible punctuation and control characters are removed/replaced; Windows reserved names are protected; and filesystem length limits are applied. The policy does not transliterate Unicode to ASCII because that would silently change user-visible names and can create collisions such as `Café`/`Cafe`.

The logical metadata remains separate from the physical name, and ZIP extraction rejects NFC/case-fold collisions before writing. This gives the pipeline a single Unicode contract from archive entry to generated filesystem artifact.

The naming policy is covered by focused functional cases; the final physical boundary applies the project-wide cross-platform policy.

ZIP extraction performs its own security validation before writing, including traversal, absolute/UNC paths, symlinks, reserved components and Unicode/case collisions. Generated output folders and artifacts pass through the same physical naming boundary afterwards.

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
7. Logical naming metadata must remain distinguishable from physical filesystem names.
8. Unicode normalization must be canonical and lossless; safety must be achieved by rejecting or replacing only filesystem-invalid syntax, never by transliterating user content.
