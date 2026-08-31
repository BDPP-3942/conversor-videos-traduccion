# Release 1.4.0 — E2E Matrix

The release E2E suite uses real subprocess entry points, temporary local storage, deterministic test adapters for STT/translation, and the system ffmpeg binary. Google Drive and rclone are represented by their public `StorageProvider` contract in isolated tests; no production credentials are required.

| Caso de uso | Entry point | Resultado esperado | Validación |
|---|---|---|---|
| Procesamiento normal | `video-translation-pipeline run` | success | real local pipeline E2E |
| Dry run | `video-translation-pipeline run --dry-run` | no side effects | real subprocess |
| AUTO concurrency | `video-translation-pipeline run --dry-run --parallel-videos 0` | safe effective concurrency | real subprocess |
| Explicit concurrency | `video-translation-pipeline run --dry-run --parallel-videos 1` | exactly 1 | resource contract tests |
| Excessive concurrency | `video-translation-pipeline run --dry-run --parallel-videos 999` | clamped below request | real subprocess |
| Resume | `video-translation-pipeline run` | reuse valid artifacts | pipeline regression suite |
| Resume invalid artifact | `video-translation-pipeline run` | reprocess invalid artifact | pipeline regression suite |
| Regeneration success | `video-translation-regenerate` | new valid result, backup removed | real local pipeline E2E |
| Regeneration failure | `video-translation-regenerate` | previous result restored | real local pipeline E2E |
| TTS CLI | `video-translation-tts --help` | executable entry point | clean package validation |
| Scheduled execution | `video-translation-pipeline run --scheduled` | same common pipeline entry point | real subprocess dry-run |
| Scheduled standalone executable | `video-translation-scheduled` | not supported by current package | not applicable; no such entry point is declared |
| Local storage | `LocalStorageProvider` | success | provider tests |
| Storage failure | local provider | correct failure | provider tests |
| Remote storage contract | mocked Google/rclone providers | same backup/restore/delete contract | provider contract tests |
| Duplicate | normal pipeline | skip/reuse correctly | regression suite |
| Partial translation | normal pipeline | partial state | regression suite |
| Cleanup | pipeline | temporary workspace cleaned | pipeline regression suite |

## E2E boundary

The subprocess E2E tests deliberately replace only the external STT and translation adapters with deterministic test adapters. The `MediaPipeline`, local storage provider, extraction, ffmpeg media conversion, manifest handling, regeneration orchestration and CLI entry points remain real. This keeps the suite deterministic without requiring model downloads, API keys, GPU hardware or Internet access.
