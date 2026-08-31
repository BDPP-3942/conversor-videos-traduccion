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

## Environment overrides

Common variables include:

```dotenv
STORAGE_PROVIDER=local
SOURCE_URI=local://storage/input
TARGET_URI=local://storage/output
SOURCE_LANG=es
TARGET_LANG=en
WHISPER_MODEL=auto
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
TRANSLATION_PROVIDER=mistral
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
TTS_ENABLED=false
```

See `.env.example` for the complete currently supported environment-variable surface. Do not commit `.env` or provider credentials.

## Provider selection

The default active provider is local. Cloud providers use persistent profiles and runtime state. Use the provider CLI rather than manually editing secrets:

```bash
python main.py provider list
python main.py provider use --help
```

## Important defaults

- Resume: enabled.
- Automatic local output deduplication: disabled.
- TTS: disabled.
- WebM generation: enabled.
- rclone automatic update: disabled.
- Whisper silence threshold: 1500 ms.
