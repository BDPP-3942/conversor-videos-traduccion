# Troubleshooting

Start with the diagnostic command:

```bash
python main.py doctor
```

Then reproduce the problem with the smallest relevant operation and inspect `storage/logs/pipeline.log`.

## Common problems

### Unsupported Python

Use Python 3.11, 3.12 or 3.13. The package explicitly rejects Python versions outside `>=3.11,<3.14`.

### FFmpeg unavailable

Run `doctor`. Check the configured FFmpeg path (`ffmpeg.bin` / `FFMPEG_BIN`) and confirm that the selected executable is accessible to the execution account.

### Translation is unavailable

Check provider credentials, network access, quotas, retry/fallback configuration and the provider-specific documentation. Application startup alone does not prove that a provider can translate a request.

### TTS assets are missing

If TTS is enabled, verify the `[tts]` dependency and both configured assets:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

The setup helper can bootstrap them when TTS is enabled.

### Scheduled execution fails but manual execution works

Check the scheduler's working directory, account permissions, environment loading, absolute/relative paths, credentials, model files, FFmpeg access and logs. Scheduled mode must not depend on an interactive browser or shell session.

### Existing output is regenerated

Check `resume_enabled`, manifests, artifact validation and naming normalization. Do not disable resume as a first troubleshooting step.

### Subtitle/TTS synchronization fails

Validate both VTT files. Cues with `start >= end` are invalid. Repair/reprocess subtitles before retrying TTS; do not manually shift later cues to hide an invalid interval.

### Duplicate deletion looks unsafe

Stop before `delete`. Review `storage/state/dedupe_plan.json`, use `duplicates delete --dry-run`, and only execute deletion after confirming the plan.
