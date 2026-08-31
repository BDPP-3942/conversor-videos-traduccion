# Installation and setup

## Requirements

- Python 3.11, 3.12 or 3.13 (`>=3.11,<3.14`).
- Internet access for package/model/provider downloads as applicable.
- Disk space for media, Whisper/TTS assets and generated output.
- Optional provider dependencies for Google Drive.
- rclone support can use the project's managed binary.

FFmpeg is supplied through the `imageio-ffmpeg` dependency unless an explicit executable is configured.

## Install

Clone the repository:

```bash
git clone https://github.com/BDPP-3942/conversor-videos-traduccion.git
cd conversor-videos-traduccion
```

### macOS/Linux

```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

Optional setup flags supported by the script are `--cloud`, `--rclone`, `--tts` and `--prefetch-whisper`.

### Windows

```bat
scripts\setup_env.bat
```

The Windows script provides the corresponding environment setup; use `scripts\setup_env.bat --help` only if the installed version adds help handling.

### Manual virtual environment

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional extras are declared in `pyproject.toml`:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[google]"
python -m pip install -e ".[tts]"
python -m pip install -e ".[package]"
```

They can be combined, for example `.[tts,google,dev,package]`.

## Configuration

The default configuration is in `config/app.toml`. `.env.default` supplies environment defaults and `.env.example` documents environment overrides.

```bash
cp .env.example .env
```

On Windows:

```bat
copy .env.example .env
```

Do not commit `.env`, credentials, provider profiles or model weights.

## Runtime directories

The repository already contains placeholders for the runtime layout:

```text
storage/
├── input/
├── work/
├── output/
│   └── _manifests/
├── archive/
├── failures/
├── logs/
└── state/
```

If a checkout lacks a directory, create it under `storage/`; logs are written to `storage/logs/`, not a top-level `logs/` directory.

## Translation providers

The default processing configuration uses Mistral with DeepL and MyMemory fallback. Provider credentials are configured through the environment/profile mechanisms documented in [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md).

## TTS

TTS is disabled by default. When enabled, the local provider is Kokoro through `kokoro-onnx`. The setup helper downloads the configured default assets when TTS is enabled:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

Equivalent explicit installation:

```bash
python -m pip install -e ".[tts]"
python scripts/setup_tts.py --enable
```

Custom asset locations can be configured with `TTS_MODEL_PATH` and `TTS_VOICES_PATH`.

## Google Drive and rclone

Google Drive requires the optional Google dependency and a provider profile. The interactive setup is:

```bash
python main.py provider setup-google --help
```

rclone can be bootstrapped and configured through the provider CLI:

```bash
python main.py provider bootstrap
python main.py provider setup-rclone --help
```

The managed rclone binary is stored under `tools/rclone/`; its configuration is under `secrets/rclone/rclone.conf` by default.

## Validate installation

```bash
python main.py doctor
python main.py --help
python main.py run --help
python main.py reprocess-subtitles --help
python main.py run --dry-run
```

For development checks:

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

## First run

For local processing, place a supported video or ZIP in `storage/input/` and run:

```bash
python main.py run
```

The wrapper equivalents are `scripts/run_local.sh` and `scripts\run_local.bat`.

## Existing results

Do not blindly reinsert already processed sources. Inspect the existing output and use the duplicate/subtitle recovery workflows when appropriate:

```bash
python main.py duplicates scan
python main.py duplicates analyze
python main.py reprocess-subtitles --help
```

See [RESUME.md](RESUME.md) and [SUBTITLES.md](SUBTITLES.md).

## Upgrade

1. Stop scheduled execution.
2. Back up `storage/output`, `storage/archive`, `storage/state`, manifests and provider profiles.
3. Update source with `git pull`.
4. Update/recreate the Python environment if dependencies changed.
5. Run `python main.py doctor` and `python main.py run --dry-run`.
6. Test a representative input.
7. Re-enable scheduling.

Do not delete manifests or outputs during an upgrade unless a documented migration requires it.

## Packaging

Install the packaging extra and use the platform-specific build script:

```bash
python -m pip install -e ".[package]"
./scripts/build_linux.sh
```

Windows:

```bat
python -m pip install -e ".[package]"
scripts\build_windows.bat
```

See [PACKAGING.md](PACKAGING.md).
