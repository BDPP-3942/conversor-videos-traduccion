# Installation and setup

## Requirements

- Python 3.11, 3.12 or 3.13 (`>=3.11,<3.14`).
- Internet access for package/model/provider downloads as applicable.
- Disk space for media, Whisper/TTS assets and generated output.
- Optional Google dependency for Google Drive.
- rclone is an external executable; the project can bootstrap and manage its own binary under `tools/rclone/`.

FFmpeg is supplied through the `imageio-ffmpeg` dependency unless an explicit executable is configured.

## Install

Clone the repository and create the Python environment using the setup scripts or the manual virtual-environment procedure below.

### macOS/Linux

```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

### Windows

```bat
scripts\setup_env.bat
```

The setup scripts accept `--cloud`, `--rclone`, `--tts` and `--prefetch-whisper`.

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

## NVIDIA / Whisper

NVIDIA support is optional. The project does not assume that `nvidia-smi` alone means that Whisper can use the GPU.

On a machine with an NVIDIA GPU, `WHISPER_DEVICE=auto` performs a runtime check of the NVIDIA driver, CUDA libraries and CTranslate2 before selecting CUDA. The project currently uses `faster-whisper>=1.2.1,<1.3` with `ctranslate2>=4.8.2,<4.9`, and the supported GPU runtime path requires CUDA 12 plus cuBLAS CUDA 12 and cuDNN 9 CUDA 12.

A full CUDA Toolkit is not required just to run the inference runtime. If the required runtime libraries are missing, an interactive Whisper initialization reports the requirements and proposed managed location (`tools/cuda/python/`) and asks for explicit confirmation before installing the NVIDIA Python runtime packages. The driver is never replaced by this installation.

See [`docs/CUDA.md`](CUDA.md) for the complete compatibility, diagnostic and cleanup procedure.

## Configuration

The default configuration is in `config/app.toml`. `.env.default` supplies environment defaults and `.env.example` documents overrides.

```bash
cp .env.example .env
```

On Windows:

```bat
copy .env.example .env
```

Do not commit `.env`, credentials, provider profiles or model weights.

## Local translation model

The optional local Spanish→English model is prepared explicitly:

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

It is stored under `tools/models/translation/`. See [`docs/LOCAL_TRANSLATION.md`](LOCAL_TRANSLATION.md) for model integrity, licensing and offline operation.

## Naming and existing output migration

The naming policy is part of the application core rather than an installation option. It separates logical course/resource metadata from physical filesystem names.

The physical form is `<curso_o_contenedor>x<nombre_sanitizado>`, where `x` is the scope separator and `_` is the word separator. Physical names normalize whitespace and separator hyphens, incompatible punctuation and controls, Unicode diacritics, Windows reserved names and filesystem length.

## Runtime directories

The runtime layout includes `storage/input/`, `storage/work/`, `storage/output/`, `storage/archive/`, `storage/failures/`, `storage/logs/` and `storage/state/`. Optional managed resources are kept outside those data directories under `tools/`.

## Translation providers

The default processing configuration uses the provider declared in `config/app.toml` with the configured fallback chain. See `docs/TRANSLATION_PROVIDERS.md`.

## TTS

TTS is disabled by default. When enabled, install the `[tts]` extra and prepare the configured Kokoro assets. See `docs/TTS.md`.

## Google Drive and rclone

Google Drive requires the `[google]` extra and a provider profile. rclone is managed separately under `tools/rclone/` and its configuration is stored under `secrets/rclone/` by default.

## Validate installation

```bash
python main.py doctor
python main.py --help
python main.py run --help
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

For local processing, place a supported video or ZIP in `storage/input/` and run `python main.py run`.

## Cleanup / uninstall

Managed resources can be removed independently:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
python scripts/manage_runtime_resources.py cuda cleanup
```

These commands do not uninstall a global NVIDIA driver or CUDA Toolkit and do not delete project data. See [`docs/UNINSTALLATION.md`](UNINSTALLATION.md) for the complete procedure.

## Upgrade

1. Stop scheduled execution.
2. Back up outputs, manifests, state and provider profiles.
3. Update source with `git pull`.
4. Update/recreate the Python environment if dependencies changed.
5. Run `python main.py doctor` and `python main.py run --dry-run`.
6. Test a representative input.
7. Re-enable scheduling.

Do not delete manifests or outputs during an upgrade unless a documented migration requires it.

## Packaging

See `docs/PACKAGING.md` for Windows and Linux packaging procedures and optional resource handling.
