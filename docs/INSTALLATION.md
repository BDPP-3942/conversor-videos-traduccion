# Installation and setup

## Requirements

- Python 3.11, 3.12 or 3.13 (`>=3.11,<3.14`).
- Internet access only when packages, Whisper models, local translation models or remote providers need to be prepared/used.
- Disk space for media, Whisper/TTS assets, the optional local translation model and generated output.
- Optional Google dependency for Google Drive.
- rclone is an external executable; the project can bootstrap and manage its own binary under `tools/rclone/`.

FFmpeg is supplied through the `imageio-ffmpeg` dependency unless an explicit executable is configured.

## Install

Clone the repository and install the project in a virtual environment:

```bash
git clone https://github.com/BDPP-3942/conversor-videos-traduccion.git
cd conversor-videos-traduccion
python -m venv .venv
```

Activate the environment and install:

```bash
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

The project pins the tested minor lines for `faster-whisper` and CTranslate2. The CPU installation does not require NVIDIA or the CUDA Toolkit.

Optional extras are declared in `pyproject.toml`:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[google]"
python -m pip install -e ".[tts]"
python -m pip install -e ".[package]"
```

They can be combined, for example `.[tts,google,dev,package]`.

## NVIDIA/CUDA

NVIDIA support is optional. The runtime is validated in this order:

```text
NVIDIA driver → CUDA dependencies → CTranslate2 → faster-whisper
```

Do not install the complete CUDA Toolkit solely because the application detects an NVIDIA GPU. The selected CTranslate2 build must have a compatible CUDA runtime. If GPU initialization fails, Whisper falls back once to CPU `int8` when CPU fallback is enabled by the runtime policy.

The application does not automatically modify the global `PATH`. Managed resources, when introduced, remain under the application resource directory.

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

## Local translation model

The bundled offline provider currently supports Spanish→English using a pinned CTranslate2 INT8 OPUS-MT conversion. It is optional at runtime but is part of the fallback chain when configured.

Prepare it explicitly:

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

The download process reports repository/revision, approximate size (~82.5 MiB), destination, reason and license before confirmation. It uses HTTPS, a pinned revision, temporary files, size limits and SHA-256 verification for the large model files. Existing valid copies are reused.

After preparation, the pipeline can run without Internet for the local translation step:

```env
TRANSLATION_PROVIDER=local
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
```

Ollama and LM Studio are not required.

Cleanup is explicit:

```bash
python scripts/manage_local_translation.py cleanup
```

This removes only the managed local translation model.

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

tools/
├── models/
│   └── translation/
└── ...
```

Do not place credentials in `tools/`.

## Translation providers

See [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md) for local/remote providers, fallback and batching.

## TTS

TTS is disabled by default. When enabled, the local provider is Kokoro through `kokoro-onnx`.

## Google Drive and rclone

Google Drive requires the `[google]` extra and a provider profile. rclone remains an external managed executable as documented in the existing provider setup.

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
ruff check . --select S
ruff format --check .
python -m compileall .
python -m pip check
```

## First run

For local processing, place a supported video or ZIP in `storage/input/` and run:

```bash
python main.py run
```

The wrapper equivalents are `scripts/run_local.sh` and `scripts\run_local.bat`.

## Existing results

Do not blindly reinsert already processed sources. Inspect the existing output and use the duplicate/subtitle recovery workflows when appropriate.

## Upgrade

1. Stop scheduled execution.
2. Back up `storage/output`, `storage/archive`, `storage/state`, manifests and provider profiles.
3. Update source with `git pull`.
4. Update/recreate the Python environment if dependencies changed.
5. Run `python main.py doctor` and `python main.py run --dry-run`.
6. Validate local model status if it is part of the configured provider chain.
7. Test a representative input.
8. Re-enable scheduling.

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

The local translation model is not bundled into the Python wheel; it is managed as an external resource under `tools/models/translation/`.
