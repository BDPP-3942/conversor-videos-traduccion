# Speech-to-text (STT)

STT uses `faster-whisper`. The selected model, device, compute type, beam size, CPU threads, VAD behavior and initial prompt are configurable.

Defaults in `config/app.toml` include automatic model/device/compute selection, beam size `5`, VAD enabled and a minimum silence duration of `1500` ms. `.env.example` exposes explicit environment overrides.

## Segmentation

Whisper timestamps are used to construct subtitle cues. The pipeline can split cues around significant detected silences. Final intervals are validated before a VTT is accepted.

The invariant is:

```text
start < end
```

Cues violating the invariant are not propagated as usable subtitles.

## Model prefetch

To initialize/download the automatically selected model:

```bash
python main.py prefetch-whisper
```

The model is not bundled into the repository by default.

## Reprocessing

If an existing original VTT is missing or invalid but the normal video exists, `reprocess-subtitles --stt-only` can regenerate the transcription without regenerating the normal video.
