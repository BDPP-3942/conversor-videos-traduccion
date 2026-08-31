# Processing pipeline

The common pipeline processes each input through independently recoverable stages. When multiple videos are processed in one run, the runtime determines the effective video concurrency before creating the workers.

```text
input video / ZIP
      ↓
validation + extraction
      ↓
media normalization
      ↓
STT + silence-aware segmentation
      ↓
original VTT validation
      ↓
translation
      ↓
translated VTT validation
      ├── subtitles / normal video
      └── optional TTS
              ↓
          cue audio
              ↓
          MP4/WebM TTS
              ↓
       artifact validation
              ↓
           manifest
```

The exact stages reused or skipped depend on valid existing artifacts and the configured resume policy.

## Video concurrency

For concurrent video processing, `max_parallel_videos` is treated as an upper bound. In the current `main` implementation, `0` means AUTO: the runtime resolves the effective Whisper configuration and derives a conservative concurrency ceiling from CPU and available RAM, also considering available GPU memory when CUDA is selected. A positive configured value can be clamped to that ceiling, while `1` remains single-worker execution.

This resource-aware scheduling of video workers was introduced after the published `1.2.2` release by PR #20. It is therefore part of current `main` behavior and must not be attributed retroactively to release `1.2.2`.

## Temporal invariant

Every generated subtitle cue must satisfy `start < end`. Translation changes cue text but preserves `start`/`end`. TTS uses the translated, validated VTT as its timing source and preserves gaps as silence.

## Failure and recovery

- Missing/invalid artifacts are candidates for regeneration.
- Valid artifacts are reused when the stage permits it.
- Subtitle repair does not regenerate the normal video.
- A TTS failure does not delete valid normal-video or subtitle artifacts.
- A runtime lock prevents overlapping pipeline executions.
