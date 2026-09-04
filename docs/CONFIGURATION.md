# Configuration

Configuration is loaded from `config/app.toml` with environment overrides. `.env.default` contains defaults and `.env.example` documents supported environment variables.

## Main sections

- `[app]`: provider, source/target URIs, source/target languages and log level.
- `[local]`: local source retention and input age policy.
- `[google_drive]`: Drive folder IDs and transcription subdirectory.
- `[rclone]`: managed binary/config paths and default remote.
- `[providers]`: persistent provider profile directory.
- `[runtime]`: resource tuning, run lock, rclone bootstrap/update.
- `[processing]`: Whisper/STT and translation behavior, ZIP safety limits and concurrency.
- `[workflow]`: resume, naming migration, duplicate handling and video parallelism.
- `[ffmpeg]`: media generation and WebM settings.
- `[tts]`: optional Kokoro TTS settings.

The local translation provider has an additional environment-only configuration surface (`LOCAL_TRANSLATION_*`). These settings are intentionally not duplicated in `config/app.toml`; they are consumed as environment overrides by the local provider.

## Environment overrides

Common variables include:

```dotenv
STORAGE_PROVIDER=local
SOURCE_URI=local://storage/input
TARGET_URI=local://storage/output
SOURCE_LANG=es
TARGET_LANG=en
WHISPER_MODEL=auto
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto
TRANSLATION_PROVIDER=mistral
TRANSLATION_FALLBACK_PROVIDERS=local,deepl,mymemory
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
TTS_ENABLED=false
```

The local model identity is pinned and is not an arbitrary configuration value:

```dotenv
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
```

See `.env.example` for the complete currently supported environment-variable surface. Do not commit `.env` or provider credentials.

## Provider selection

The default active provider is configured in `config/app.toml` and may be overridden by `TRANSLATION_PROVIDER`. Provider credentials are configured through the existing profile/environment mechanisms. Use the provider CLI rather than manually editing secrets:

```bash
python main.py provider list
python main.py provider use --help
```

## Naming configuration and policy

Naming is deliberately not configured through a free-form replacement template. The application owns a deterministic policy so that ZIP extraction, generated output folders and generated artifacts use the same physical filesystem rules.

The canonical physical naming contract is:

```text
<curso_o_contenedor>_<nombre_sanitizado>
```

`_` is the canonical separator between scope blocks and between words. Hyphens, whitespace and other incompatible separators are normalized to `_`; accents and unsafe filesystem characters are normalized as part of the physical-name boundary. The historical `x` scope separator is accepted only as legacy input and is migrated to `_` when existing output-name normalization is enabled.

The `normalize_legacy_names` workflow setting controls migration of already existing output names. It does not change the naming rules themselves. When enabled, migration is performed before normal processing and must not silently overwrite an existing destination. Legacy names are analyzed conservatively and only renamed when the canonical target is unambiguous.

## Video concurrency

`max_parallel_videos` controls the upper bound for concurrent video processing. Its effective value is calculated from the resolved Whisper device/model, CPU threads, available RAM and, when CUDA is used, available GPU memory.

- `0` means **AUTO**: the application selects a conservative safe concurrency level from the detected hardware.
- A positive value is an **upper bound**, not a guarantee. If it exceeds the safe hardware ceiling, it is clamped automatically.
- `1` explicitly preserves single-worker execution.

The resource calculation intentionally leaves headroom for the operating system, Python and FFmpeg. The effective value can therefore be lower than the configured value even when the configuration is valid.

This behavior was introduced after the `1.2.2` release by PR #20 (`perf: enforce safe video concurrency`). It is part of the current `main` behavior, but it is **not part of the published `1.2.2` release**.

## Important defaults

- Resume: enabled.
- Automatic local output deduplication: disabled.
- TTS: disabled.
- WebM generation: enabled.
- rclone automatic update: disabled.
- Whisper device: `auto`.
- Whisper compute type: `auto`.
- Whisper silence threshold: 1500 ms.
- Local translation auto-download: disabled.
- Local translation device: `auto`.
- Local translation compute type: `auto`.
- Local translation beam size: 2.
