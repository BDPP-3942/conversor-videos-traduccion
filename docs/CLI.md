# CLI reference

Run from the repository root with `python main.py`, or use the installed console entry point `video-translation-pipeline` after installation.

## Main commands

```bash
python main.py --help
python main.py run --help
python main.py doctor
python main.py init
python main.py prefetch-whisper
```

### Processing

```bash
python main.py run
python main.py run --dry-run
python main.py run --scheduled
```

`run --scheduled` uses the persisted active provider configuration and refuses provider/source/target overrides.

Useful processing overrides include `--provider`, `--source`, `--target`, `--no-resume`, `--parallel-videos`, `--translation-batch-size`, `--whisper-beam-size`, `--whisper-cpu-threads`, `--no-ffmpeg-copy`, `--generate-webm` and `--no-webm`. Run `python main.py run --help` for the authoritative list.

`--parallel-videos` follows the release contract `0 = AUTO`, `1 = exactly one worker`, and `N > 1 = requested upper bound`. Every explicit value is passed through the same hardware-safe calculation used by the normal pipeline; an explicit value can never exceed the safe ceiling. For example, `--parallel-videos 999` is clamped to the calculated effective limit.

### Clean regeneration

To explicitly regenerate existing video results from the original source, bypassing normal reuse decisions:

```bash
video-translation-regenerate --help
video-translation-regenerate
```

Locations may be supplied explicitly:

```bash
video-translation-regenerate \
  --source local://storage/input \
  --target local://storage/output
```

This operation is different from `run --no-resume`: regeneration first locates existing results, moves registered output folders through the public `StorageProvider` backup contract, runs the common `MediaPipeline` from the source, and removes the backups only after successful completion. The source is preserved. If processing fails, previous outputs and the previous manifest are restored where the storage backend supports the required operations.

See [`REGENERATION.md`](REGENERATION.md) for provider-specific guarantees and limitations.

### Subtitle recovery

```bash
python main.py reprocess-subtitles --help
python main.py reprocess-subtitles --all
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
```

The command can also target a specific output folder with `--output-folder` or a video with `--video`.

### Duplicate management

```bash
python main.py duplicates scan
python main.py duplicates analyze
python main.py duplicates delete --dry-run
python main.py duplicates delete
```

Use `--target` before the subcommand to select another local output directory.

### Providers

```bash
python main.py provider list
python main.py provider bootstrap
python main.py provider verify google_drive --profile default
python main.py provider verify rclone --profile default --location input
python main.py provider use --help
```

Administrative setup commands include `provider setup-google`, `provider setup-rclone`, `provider auth-rclone`, `provider update-rclone` and `provider remove`.

### Other entry points

```bash
video-subtitle-qa --help
video-translation-tts --help
video-translation-regenerate --help
```

These are installed by `pyproject.toml`; their detailed options should be obtained from their own `--help` output rather than duplicated here.

## Exit status

`run` returns `0` for success, `2` for partial completion, `1` for processing errors and `3` when readiness checks fail.
