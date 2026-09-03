# Installation and setup

## Requirements

- Python 3.11, 3.12 or 3.13 (`>=3.11,<3.14`).
- Internet access for package/model/provider downloads as applicable.
- Disk space for media, Whisper/TTS assets and generated output.
- Optional Google dependency for Google Drive.
- rclone is an external executable; the project can bootstrap and manage its own binary under `tools/rclone/`.

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

The setup script accepts exactly these optional flags: `--cloud`, `--rclone`, `--tts` and `--prefetch-whisper`.

### Windows

```bat
scripts\setup_env.bat
```

The Windows setup script accepts the same four optional flags: `--cloud`, `--rclone`, `--tts` and `--prefetch-whisper`.

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

## Naming and existing output migration

The naming policy is part of the application core rather than an installation option. It separates logical course/resource metadata from physical filesystem names.

The physical form is:

```text
<curso_o_contenedor>x<nombre_sanitizado>
```

`x` is the scope separator and `_` is the word separator. Physical names normalize whitespace and separator hyphens, incompatible punctuation and controls, Unicode diacritics, Windows reserved names and filesystem length. Existing output migration is controlled by the current `normalize_legacy_names` workflow setting and is designed to preserve content while moving only the affected output paths.

## Runtime directories

The runtime layout is:

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

If a checkout lacks a directory, create it under `storage/`; logs are written to `storage/logs/pipeline.log`.

## Translation providers

The default processing configuration uses the provider declared in `config/app.toml` (currently Mistral in the repository baseline) with the configured fallback chain. Provider credentials are configured through environment/profile mechanisms. See [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md).

## TTS

TTS is disabled by default. When enabled, the local provider is Kokoro through `kokoro-onnx`. The setup helper prepares the default assets when TTS is enabled:

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

Google Drive requires the `[google]` extra and a provider profile. The interactive setup is exposed by:

```bash
python main.py provider setup-google --help
```

rclone is not a Python dependency. The project can bootstrap its managed rclone binary and then configure a remote through the provider CLI:

```bash
python main.py provider bootstrap
python main.py provider setup-rclone --help
```

The managed binary is stored under `tools/rclone/`; its configuration is under `secrets/rclone/rclone.conf` by default.

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

The repository currently provides packaging scripts for Windows and Linux:

```bash
python -m pip install -e ".[package]"
./scripts/build_linux.sh
```

Windows:

```bat
python -m pip install -e ".[package]"
scripts\build_windows.bat
```

There is no repository packaging script for macOS at present. See [PACKAGING.md](PACKAGING.md).
