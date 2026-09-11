# Configuration

Configuration is loaded from `config/app.toml` with environment overrides. `.env.default` contains defaults and `.env.example` documents supported environment variables.

## Main sections

- `[app]`: provider, source/target URIs, source/target languages and log level.
- `[local]`: local source retention and input age policy.
- `[google_drive]`: Drive folder IDs and transcription subdirectory.
- `[rclone]`: managed binary/config paths and default remote.
- `[providers]`: persistent provider profile directory.
- `[runtime]`: resource tuning, run lock, rclone bootstrap/update.
- `[processing]`: Whisper/STT, local translation model selection, translation behavior and ZIP safety limits.
- `[workflow]`: resume, naming migration, duplicate handling and video parallelism.
- `[ffmpeg]`: media generation and WebM settings.
- `[tts]`: optional Kokoro TTS settings.

The local translation model is configurable both from `config/app.toml` and through the corresponding `LOCAL_TRANSLATION_*` environment overrides. Two pinned models are supported: MADLAD-400 3B as the default quality-oriented model and OPUS-MT as the lightweight compatibility model. Repository and revision must match the selected model; arbitrary model/revision combinations are not supported.

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
LOCAL_TRANSLATION_MODEL=madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=cstr/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=12eff26f7d93623e2b2d3b5345e5863e14599dae
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
LOCAL_TRANSLATION_HF_TOKEN=
TTS_ENABLED=false
```

To select the lightweight OPUS-MT model, set the complete OPUS configuration together:

```dotenv
LOCAL_TRANSLATION_MODEL=opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
```

`LOCAL_TRANSLATION_HF_TOKEN` is optional. Public model downloads work without authentication; configure it only when the Hugging Face environment requires authentication. `HF_TOKEN` is also accepted as a standard fallback. The token is used only for the HTTPS download and is not stored with the model.

See `.env.example` for the complete currently supported environment-variable surface. Do not commit `.env` or provider credentials.

## Provider selection

The default active provider is configured in `config/app.toml` and may be overridden by `TRANSLATION_PROVIDER`. Provider credentials are configured through the existing profile/environment mechanisms. Use the provider CLI rather than manually editing secrets:

```bash
python main.py provider list
python main.py provider use --help
```

## Naming configuration and policy

Naming is deliberately not configured through a free-form replacement template. The application owns a deterministic policy so that ZIP extraction, generated output folders and generated artifacts use the same physical filesystem rules.

The logical naming contract is represented as:

```text
<curso_o_contenedor>x<nombre_normalizado>
```

`x` separates scope; `_` separates words inside each block. The canonical physical name is intended for web URLs and metadata and therefore is normalized to lowercase with `casefold()`. Unicode is canonically decomposed with NFD, combining diacritical marks are removed and the result is recomposed with NFC (`niño` -> `nino`, `Vídeo` -> `video`, `õ` -> `o`). Emoji/Unicode symbols are omitted. Letters from other scripts are retained when they are not diacritics or symbols. Filesystem-invalid characters, control characters, Windows reserved components and filesystem length limits are handled by the physical filesystem boundary as well.

This normalization is intentionally deterministic and idempotent. It does not attempt heuristic repair of mojibake or otherwise guess the user's intended spelling.

The `normalize_legacy_names` workflow setting controls migration of already existing output names. It does not change the naming rules themselves. When enabled, migration is performed before normal processing and must not silently overwrite an existing destination.

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
- WebM generation: disabled by default; `--generate-webm` explicitly enables it.
- rclone automatic update: disabled.
- Whisper device: `auto`.
- Whisper compute type: `auto`.
- Whisper VAD silence threshold: 2000 ms.
- Whisper subtitle split silence threshold: 1000 ms.
- Local translation auto-download: disabled.
- Local translation model: MADLAD-400 3B CT2 INT8.
- Local translation device: `auto`.
- Local translation compute type: `auto`.
- Local translation beam size: 2.
