# Processing pipeline

The common pipeline processes each input through independently recoverable stages.

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

## Temporal invariant

Every generated subtitle cue must satisfy `start < end`. Translation changes cue text but preserves `start`/`end`. TTS uses the translated, validated VTT as its timing source and preserves gaps as silence.

## Failure and recovery

- Missing/invalid artifacts are candidates for regeneration.
- Valid artifacts are reused when the stage permits it.
- Subtitle repair does not regenerate the normal video.
- A TTS failure does not delete valid normal-video or subtitle artifacts.
- A runtime lock prevents overlapping pipeline executions.
