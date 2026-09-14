# Installation and setup

## Requirements

- Python 3.11, 3.12 or 3.13 (`>=3.11,<3.14`). The setup scripts can install the requested Python through the project-managed `uv` tool.
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

The setup script first uses a project-managed `tools/uv/uv` executable when one already exists. Otherwise it uses `uv` from `PATH`; if neither is available, it downloads the official uv installer and creates the project-managed copy under `tools/uv/`. The local binary is ignored by Git and the installer is invoked in unmanaged mode, so the setup does not modify the user's shell profile.

The setup script accepts these optional flags:

- `--cloud` — install the Google Drive extra.
- `--rclone` — bootstrap the managed rclone binary.
- `--tts` — install and enable the optional Kokoro TTS dependency/assets.
- `--prefetch-whisper` — prefetch the Whisper model selected by the application.
- `--local-translation` — download and validate the configured pinned local translation model during the same setup run.

For a complete local setup including the default MADLAD-400 3B translation model:

```bash
./scripts/setup_env.sh --local-translation
```

The `--local-translation` flag is deliberately opt-in because the default MADLAD model is approximately 2.95 GB. If it is omitted, the environment is fully prepared but the local translation weights are not downloaded. They can be installed later with the existing command:

```bash
uv run python scripts/manage_local_translation.py download
```

Status and a real runtime benchmark can then be checked with:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

The project-managed `uv` binary is not committed to the repository. It is downloaded for the host platform when required, while the Python environment remains the normal project `.venv` managed by uv.

### Windows

```bat
scripts\setup_env.bat
```

The Windows setup script implements the same uv resolution order and downloads a project-managed `tools\uv\uv.exe` when no system `uv.exe` is available. It accepts the same six optional flags listed above.

### Manual virtual environment

The setup scripts are the preferred installation path because they bootstrap uv when necessary. A manual installation remains supported:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional extras are declared in `pyproject.toml`. The repository currently defines `google`, `tts` and `rclone` extras; development, audit and packaging dependencies are uv dependency groups:

```bash
python -m pip install -e ".[google]"
python -m pip install -e ".[tts]"
uv sync --group dev
uv sync --group audit
```

## Release 1.8.1

`1.8.1` is the next PATCH release after the published `1.8.0`. It improves fresh-checkout setup by making uv self-bootstrapping when no system uv is available, adds an explicit one-command option for preparing the pinned local translation model, and preserves the standalone model download command for deferred installation.

The runtime dependency ranges remain `faster-whisper>=1.2.1,<1.3` and `ctranslate2>=4.8.2,<4.9`.

## NVIDIA/CUDA and Whisper

NVIDIA acceleration is optional. The `1.8.1` release does not change the GPU runtime architecture consolidated through the previous releases; the GPU path requires CUDA 12, cuBLAS for CUDA 12 and cuDNN 9 for CUDA 12.

`WHISPER_DEVICE=auto` does not treat the presence of `nvidia-smi` as sufficient. At Whisper initialization the project checks the NVIDIA driver, searches for an installed CUDA Toolkit, checks the required NVIDIA runtime libraries and asks CTranslate2 whether a CUDA device and supported compute types are actually available.

If an NVIDIA GPU is detected but the runtime is incomplete, an interactive execution reports the detected versions, requirements, approximate installation location and reason for failure, then asks whether the managed NVIDIA runtime should be installed. The managed libraries are placed under `tools/cuda/python/`; the NVIDIA driver is not replaced and a full CUDA Toolkit is not installed by this operation. In unattended execution no installation prompt is shown and the existing CPU fallback is used.

A CUDA Toolkit installed globally is not automatically replaced or removed. It may be used when compatible, while the managed runtime can provide the required user-space libraries without modifying the global Toolkit.

See [`docs/CUDA.md`](CUDA.md) for diagnostics, compatibility and cleanup.

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

Managed optional model/runtime resources are kept under `tools/` and are deliberately separate from project data. The project-managed uv executable, when bootstrapped, lives under `tools/uv/` and is ignored by Git.

## Translation providers

The default processing configuration uses the provider declared in `config/app.toml` (currently Mistral in the repository baseline) with the configured fallback chain. Provider credentials are configured through environment/profile mechanisms. See [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md).

For the optional offline local provider, the preferred setup path is now:

```bash
./scripts/setup_env.sh --local-translation
```

That flag runs the same validated download flow as the standalone manager after the Python environment has been prepared. It uses the pinned model configured by the checkout; the default is MADLAD-400 3B CT2 INT8. If you prefer to defer the large model download, omit the flag and run it later:

```bash
uv run python scripts/manage_local_translation.py download
```

The local-model preparation validates the selected pinned model before activation. MADLAD requires `model.bin`, `sentencepiece.model`, `config.json` and `shared_vocabulary.json`; OPUS-MT retains its `model.bin`, `source.spm`, `target.spm` and JSON metadata contract. The MADLAD installation is bounded by the project installation budget and model integrity is checked before offline use.

The model is stored below `tools/models/translation/`. See [LOCAL_TRANSLATION.md](LOCAL_TRANSLATION.md).

After downloading, validate the actual runtime rather than only checking file presence:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

The benchmark initializes CTranslate2 + SentencePiece and executes a real translation with the prepared model.

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
uv run python main.py provider setup-google --help
```

rclone is not a Python dependency. The project can bootstrap its managed rclone binary and then configure a remote through the provider CLI:

```bash
uv run python main.py provider bootstrap
uv run python main.py provider setup-rclone --help
```

The managed binary is stored under `tools/rclone/`; its configuration is under `secrets/rclone/rclone.conf` by default.

## Validate installation

```bash
uv run python main.py doctor
uv run python main.py --help
uv run python main.py run --help
uv run python main.py reprocess-subtitles --help
uv run python main.py run --dry-run
```

For development checks:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall .
```

## First run

For local processing, place a supported video or ZIP in `storage/input/` and run:

```bash
uv run python main.py run
```

The wrapper equivalents are `scripts/run_local.sh` and `scripts\run_local.bat`.

## Existing results

Do not blindly reinsert already processed sources. Inspect the existing output and use the duplicate/subtitle recovery workflows when appropriate:

```bash
uv run python main.py duplicates scan
uv run python main.py duplicates analyze
uv run python main.py reprocess-subtitles --help
```

See [RESUME.md](RESUME.md) and [SUBTITLES.md](SUBTITLES.md).

## Cleanup and uninstall

Project-managed resources can be inspected or removed independently:

```bash
uv run python scripts/manage_runtime_resources.py translation-model status
uv run python scripts/manage_runtime_resources.py translation-model cleanup
uv run python scripts/manage_runtime_resources.py cuda status
uv run python scripts/manage_runtime_resources.py cuda cleanup
```

These commands do not delete `storage/` data, source code, manifests or credentials. The CUDA cleanup only removes the project's `tools/cuda/` directory; it does not uninstall a global NVIDIA driver or CUDA Toolkit. See [UNINSTALLATION.md](UNINSTALLATION.md).

If the project-managed uv tool needs to be removed, delete `tools/uv/`; this has no effect on a separately installed system uv.

## Upgrade

1. Stop scheduled execution.
2. Back up `storage/output`, `storage/archive`, `storage/state`, manifests and provider profiles.
3. Update source with `git pull`.
4. Re-run `./scripts/setup_env.sh` (or `scripts\setup_env.bat`) if the dependency graph or setup behavior changed.
5. Run `uv run python main.py doctor` and `uv run python main.py run --dry-run`.
6. Test a representative input.
7. Re-enable scheduling.

Do not delete manifests or outputs during an upgrade unless a documented migration requires it.

## Packaging

The repository currently provides packaging scripts for Windows and Linux:

```bash
uv sync --group dev --extra tts
./scripts/build_linux.sh
```

Windows:

```bat
uv sync --group dev --extra tts
scripts\build_windows.bat
```

There is no repository packaging script for macOS at present. See [PACKAGING.md](PACKAGING.md).
