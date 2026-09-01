# Release 1.4.1 — E2E Matrix

The release E2E suite uses real subprocess execution, temporary local storage, deterministic test adapters for external STT/translation boundaries, the real `MediaPipeline`, and ffmpeg. Google Drive and rclone are represented by their public `StorageProvider` contract in isolated tests; production credentials are not required.

| Caso de uso | Script / Entry point | Resultado esperado | Validación |
|---|---|---|---|
| Procesamiento normal | `video-translation-pipeline run` / `scripts/run_local.*` | success | real local pipeline E2E |
| Dry run | `video-translation-pipeline run --dry-run` | no side effects | real subprocess |
| AUTO concurrency | `video-translation-pipeline run --dry-run --parallel-videos 0` | safe effective concurrency | real subprocess |
| Explicit concurrency | `video-translation-pipeline run --dry-run --parallel-videos 1` | exactly 1 | CLI/resource regression |
| Excessive concurrency | `video-translation-pipeline run --dry-run --parallel-videos 999` | clamped below request | real subprocess |
| Resume | `video-translation-pipeline run` | reuse valid artifacts | pipeline regression suite |
| Resume invalid artifact | `video-translation-pipeline run` | reprocess invalid artifact | pipeline regression suite |
| Regeneration success | `scripts/run_local.sh regenerate` | new valid result, backup removed | real subprocess wrapper E2E |
| Regeneration failure | `video-translation-regenerate` | previous result restored | real subprocess entry-point E2E |
| TTS CLI | `video-translation-tts --help` | executable entry point | clean package validation |
| Scheduled execution | `scripts/run_scheduled.*` / `video-translation-pipeline run --scheduled` | same common pipeline entry point | real subprocess dry-run |
| Scheduled standalone executable | `video-translation-scheduled` | not supported by current package | NOT APPLICABLE |
| Local storage | existing pipeline/provider tests | success | provider tests |
| Storage failure | existing provider tests | correct failure | provider tests |
| Remote storage contract | public Google/rclone provider contracts | same backup/restore/delete contract | contract tests |
| Duplicate | normal pipeline | skip/reuse correctly | regression suite |
| Partial translation | normal pipeline | partial state | regression suite |
| Cleanup | common pipeline | no unsafe residue | regression suite |

## Script integration boundary

`run_local.sh` and `run_local.bat` are execution wrappers. The `regenerate` action dispatches directly to `src.regeneration`; regeneration itself owns orchestration and invokes `MediaPipeline`, which uses the public `StorageProvider` contract. The wrappers do not implement media processing, storage, rollback or concurrency logic.

## E2E boundary

The subprocess E2E tests replace only external STT and translation adapters with deterministic test adapters. The `MediaPipeline`, local storage provider, extraction, ffmpeg media conversion, manifest handling, regeneration orchestration, CLI entry points and relevant execution wrappers remain real. This keeps the suite deterministic without model downloads, API keys, GPU hardware or Internet access.

Windows `.bat` execution cannot be certified by a Linux runner and must be marked NOT VALIDATED unless a Windows execution environment is available.
