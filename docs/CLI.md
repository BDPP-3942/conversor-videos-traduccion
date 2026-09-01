# CLI reference

Run from the repository root with `python main.py`, or use the installed console entry point `video-translation-pipeline` after installation.

## Main commands

```bash
python main.py --help
python main.py run --help
python main.py doctor --help
python main.py init --help
python main.py prefetch-whisper --help
```

Every command exposing `--help` should be treated as part of the public CLI contract. The parser is authoritative for accepted options; this document explains the intended semantics and the regeneration classification.

### Processing: `run`

```bash
python main.py run
python main.py run --dry-run
python main.py run --scheduled
```

`run --scheduled` uses the persisted active provider configuration and refuses provider/source/target overrides.

#### `run` flags

| Flag | Value / default | Description |
|---|---|---|
| `--scheduled` | flag; off by default | Runs in unattended scheduled-task mode and never opens a browser or asks for input. Provider/source/target must come from the saved active configuration. |
| `--dry-run` | flag; off by default | Performs readiness validation and prints the effective readiness information without processing files. |
| `--provider` | `local`, `google_drive`, `gdrive`, `rclone`; default: active configuration | Selects the storage provider for the run. |
| `--source` | storage URI; default: active configuration | Overrides the configured source URI. It is used together with the target override contract of `run`. |
| `--target` | storage URI; default: active configuration | Overrides the configured target URI. It is used together with the source override contract of `run`. |
| `--no-retain-sources` | flag; off by default | For local storage, prevents retaining source files after normal processing. Not valid for regeneration because regeneration guarantees source preservation. |
| `--no-resume` | flag; off by default | Disables normal resume behavior for this `run`. It is not accepted by regeneration because regeneration already forces reprocessing. |
| `--no-name-migration` | flag; off by default | Disables legacy-name normalization for this execution. |
| `--parallel-videos N` | integer; `0 = AUTO` | Requests the maximum video worker count. Positive values are upper bounds and are clamped by the same hardware-safe calculation used by the pipeline. `1` keeps a single worker. |
| `--translation-batch-size N` | integer; normal configuration default when omitted | Overrides the translation request batch size for this execution. Values below 1 are normalized to the minimum valid value by the shared override implementation. |
| `--whisper-beam-size N` | integer; normal configuration default when omitted | Overrides Whisper beam size. Values below 1 are normalized to the minimum valid value by the shared override implementation. |
| `--whisper-cpu-threads N` | integer; `0` keeps automatic runtime behavior | Overrides Whisper CPU thread configuration. Negative values are normalized to `0`. |
| `--no-ffmpeg-copy` | flag; off by default | Disables the FFmpeg stream-copy optimization by setting `ffmpeg_avoid_reencode` to false. |
| `--generate-webm` | flag; off unless explicitly selected | Forces generation of the secondary WebM output. Mutually exclusive with `--no-webm`. |
| `--no-webm` | flag; off unless explicitly selected | Prevents generation of the secondary WebM output. Mutually exclusive with `--generate-webm`. |

The `run` parser is the source of truth for option names, types and choices. Defaults that are not represented by an explicit CLI override continue to come from the loaded application configuration.

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

#### Regeneration flags shared with `run`

Regeneration accepts the following `run` flags because their semantics affect the common `MediaPipeline` without conflicting with the regeneration contract:

```text
--provider
--source
--target
--no-name-migration
--parallel-videos
--translation-batch-size
--whisper-beam-size
--whisper-cpu-threads
--no-ffmpeg-copy
--generate-webm
--no-webm
```

These are not maintained as a second set of argparse definitions. Regeneration reuses the `run` actions, including type conversion, choices, defaults and help text, and delegates override application to the same `_apply_run_overrides` implementation.

The following `run` flags are intentionally **not** accepted by regeneration:

| Flag | Reason |
|---|---|
| `--scheduled` | A separate regeneration entry point already defines the operation; this flag is a `run` execution mode rather than a pipeline configuration override. |
| `--dry-run` | Regeneration has no dry-run execution path. Accepting it would imply a different operation rather than a regeneration with a configuration override. |
| `--no-retain-sources` | Contradicts the regeneration guarantee that source inputs are preserved. |
| `--no-resume` | Regeneration explicitly invokes `MediaPipeline` with `force_reprocess=True`; resume is not the selected execution mode. |

The regeneration parser also has `--config`, which selects the TOML configuration file and is the regeneration entry point's own configuration option.

This operation is different from `run --no-resume`: regeneration first locates existing results, moves registered output folders through the public `StorageProvider` backup contract, runs the common `MediaPipeline` from the source, and removes the backups only after successful completion. The source is preserved. If processing fails, previous outputs and the previous manifest are restored where the storage backend supports the required operations.

See [`REGENERATION.md`](REGENERATION.md) for provider-specific guarantees and limitations.

### Subtitle recovery

```bash
python main.py reprocess-subtitles --help
python main.py reprocess-subtitles --all
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
```

The command accepts `--stt-only` or `--translate-only` (mutually exclusive), `--output-folder`, `--all`, `--video`, `--source`, `--scheduled`, `--provider` and `--target`. See the command's own `--help` output for the authoritative parser contract.

### Duplicate management

```bash
python main.py duplicates --help
python main.py duplicates scan --help
python main.py duplicates analyze --help
python main.py duplicates delete --help
```

Use `--target` before the subcommand to select another local output directory. `duplicates delete` additionally accepts `--dry-run` to report the persisted deletion plan without modifying files.

### Providers

```bash
python main.py provider --help
python main.py provider list --help
python main.py provider verify google_drive --help
python main.py provider verify rclone --help
python main.py provider use --help
```

Administrative setup commands include `provider bootstrap`, `provider setup-google`, `provider setup-rclone`, `provider auth-rclone`, `provider update-rclone` and `provider remove`. Each subcommand's `--help` output is authoritative for required positional values, choices and optional flags.

### Other entry points

```bash
video-subtitle-qa --help
video-translation-tts --help
video-translation-regenerate --help
```

These are installed by `pyproject.toml`; their parser help is the authoritative option contract.

## Entry points

The package currently exposes:

- `video-translation-pipeline` → `main:main`
- `video-translation-regenerate` → `src.regeneration:main`
- `video-subtitle-qa` → `src.subtitle_qa_cli:main`
- `video-translation-tts` → `src.tts_cli:main`

The regeneration wrapper scripts delegate directly to `src.regeneration`, so they do not maintain a second parser or pipeline implementation.

## Exit status

`run` returns `0` for success, `2` for partial completion, `1` for processing errors and `3` when readiness checks fail. Regeneration returns `0` on successful regeneration and `3` when readiness checks fail; parser and provider contract errors terminate with a non-zero CLI error status.
