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

`--parallel-videos` controls the configured upper bound for concurrent video processing. In the current implementation, `0` means AUTO: the effective concurrency is calculated conservatively from the resolved Whisper configuration and available CPU/RAM resources, and GPU memory when CUDA is selected. Positive values may be clamped to the safe hardware ceiling; `1` remains single-worker execution.

This resource-aware behavior was introduced after the published `1.2.2` release by PR #20 and is therefore documented as current `main` behavior rather than as part of `1.2.2`.

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
```

These are installed by `pyproject.toml`; their detailed options should be obtained from their own `--help` output rather than duplicated here.

## Exit status

`run` returns `0` for success, `2` for partial completion, `1` for processing errors and `3` when readiness checks fail.
