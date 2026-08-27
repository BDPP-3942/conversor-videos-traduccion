# Installation and setup

This guide explains how to install and prepare the Video Translation Pipeline for local, unattended, packaged, and cloud-backed execution.

## 1. Requirements

- Python 3.11, 3.12, or 3.13.
- FFmpeg available through the configured executable or the `imageio-ffmpeg` dependency.
- Enough disk space for source videos, temporary processing, Whisper models, TTS models, and generated media.
- Internet access for the first installation and for any configured translation/cloud provider.
- For local TTS: the optional TTS dependency and the configured Kokoro model/voice files.
- For Google Drive: the optional Google dependency and an authorized provider profile.
- For rclone: a working rclone binary/configuration or the project's bootstrap mechanism.

The Python package declares `>=3.11,<3.14`. See `pyproject.toml` for the authoritative dependency ranges.

## 2. Clone the repository

```bash
git clone https://github.com/BDPP-3942/conversor-videos-traduccion.git
cd conversor-videos-traduccion
```

Keep production secrets, provider profiles, rclone configuration, models, and generated media outside Git-tracked source files.

## 3. Create the Python environment

### macOS / Linux

```bash
chmod +x scripts/setup_env.sh scripts/run_local.sh
./scripts/setup_env.sh
```

### Windows

```bat
scripts\setup_env.bat
```

If the setup scripts are not available in a particular distribution, create and activate a virtual environment manually and install the package:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For TTS:

```bash
python -m pip install -e ".[tts]"
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

For Google Drive support:

```bash
python -m pip install -e ".[google]"
```

For packaging:

```bash
python -m pip install -e ".[package]"
```

Multiple extras can be installed together, for example `.[tts,google,dev,package]`.

## 4. Environment variables

Copy `.env.example` to `.env` only when you need local overrides:

```bash
cp .env.example .env
```

On Windows:

```bat
copy .env.example .env
```

`.env.default` provides the default environment values. `.env` must contain only machine-specific overrides and secrets; never commit it.

### Minimum local configuration

The defaults in `.env.default` and `config/app.toml` are intended to support local processing. The important values are:

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
```

Translation credentials must be supplied for the providers that you actually enable. At least one usable translation provider/profile is required when translation is needed.

### TTS configuration

TTS is disabled by default. To use the local Kokoro provider:

```dotenv
TTS_ENABLED=true
TTS_REQUIRED=false
TTS_PROVIDER=kokoro
TTS_VOICE=af_sarah
TTS_MODEL_PATH=tools/tts/kokoro-v1.0.onnx
TTS_VOICES_PATH=tools/tts/voices-v1.0.bin
TTS_SPEED=1.0
TTS_MAX_SPEED=1.35
TTS_DURATION_TOLERANCE=0.02
TTS_SAMPLE_RATE=24000
TTS_AUDIO_BITRATE=192k
TTS_WEBM_AUDIO_BITRATE=192k
TTS_GENERATE_WEBM=true
```

The Kokoro weights are not stored in Git. Obtain model and voice files from their legitimate distribution source and place them at the configured paths, or set `TTS_MODEL_PATH` and `TTS_VOICES_PATH` to external locations.

See `docs/TTS.md` for synchronization, artifacts, licensing, and commercial-distribution considerations.

### Cloud storage

For Google Drive configure the profile and folder IDs required by `config/app.toml`/the selected provider workflow. For rclone configure the remote and configuration file. Cloud authentication must be completed before a scheduled run; scheduled execution must not depend on an interactive browser or terminal prompt.

## 5. Directory layout

The application expects a structure similar to:

```text
conversor-videos-traduccion/
├── config/
├── docs/
├── logs/
├── scripts/
├── src/
├── storage/
│   ├── input/
│   ├── work/
│   ├── output/
│   ├── archive/
│   └── state/
├── secrets/
└── tools/
    ├── rclone/
    └── tts/
```

Create missing runtime directories if your checkout does not already contain them:

```bash
mkdir -p storage/input storage/work storage/output storage/archive storage/state logs
```

On Windows, create the same directories through Explorer or `mkdir`.

Do not place real credentials, provider tokens, or model weights under Git-tracked paths unless those paths are explicitly ignored and intended for local runtime data.

## 6. Validate the installation

Run:

```bash
python main.py doctor
python main.py --help
python main.py run --help
python main.py reprocess-subtitles --help
```

For a non-destructive readiness check:

```bash
python main.py run --dry-run
```

For development validation:

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

## 7. First local run

Place a source video or supported ZIP in `storage/input/` when using local ingestion. Then run:

```bash
python main.py run
```

or use the platform wrapper:

```bash
./scripts/run_local.sh
```

On Windows:

```bat
scripts\run_local.bat
```

The pipeline is resumable. Valid existing artifacts should be reused instead of repeating completed processing stages.

## 8. Existing processed results

If you already have processed videos in `storage/output/`, do not automatically put all original videos back into `storage/input/` and run the complete pipeline. First inspect manifests and existing artifacts, scan duplicates, and use the subtitle reprocessing flow where appropriate:

```bash
python main.py duplicates scan
python main.py duplicates analyze
python main.py reprocess-subtitles --help
```

After correcting/retranslating subtitles, enable TTS and run the pipeline in resume mode using the options shown by `python main.py run --help`. The exact TTS CLI flags are intentionally not duplicated here so this guide remains aligned with the installed version.

## 9. TTS model files

For the default local provider, install the optional dependency and provide both configured files:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

Do not commit these files. For portable executables, keep them alongside the executable distribution or configure absolute/external paths as described in `docs/TTS.md`.

## 10. Google Drive and rclone

The recommended architecture performs heavy processing locally and uses cloud storage as an input/output transport. A typical flow is:

```text
cloud input
   ↓
download
storage/input
   ↓
processing
   ↓
storage/output
   ↓
validation
   ↓
cloud output
   ↓
archive/cleanup
```

Test cloud readiness before enabling unattended operation. Never delete local results solely because an upload command was started; the output must be validated and the transfer must be confirmed first.

## 11. Scheduled execution

Scheduled jobs must:

- use an absolute working directory;
- use the intended Python environment or executable;
- have access to `.env`/configuration and provider credentials;
- have access to FFmpeg, Whisper and TTS model files;
- write logs to a persistent directory;
- avoid interactive authentication;
- return meaningful process exit codes.

See `docs/UNATTENDED.md` for scheduler-specific guidance.

## 12. Building an executable

Install the package extra:

```bash
python -m pip install -e ".[package]"
```

Build using the repository's packaging configuration/scripts. TTS model weights are external resources and are not automatically embedded in PyInstaller; a portable distribution must provide them or configure external paths.

Build the executable on the target operating system. Do not assume that a Windows executable can be produced or tested from macOS/Linux, or vice versa.

## 13. Upgrading

Before upgrading a working installation:

1. Back up `storage/output`, `storage/archive`, `storage/state`, manifests, configuration, and provider profiles.
2. Stop scheduled jobs.
3. Update the repository:

```bash
git pull
```

4. Re-run the environment setup or update dependencies.
5. Run `python main.py doctor` and `python main.py run --dry-run`.
6. Test one representative job before resuming the complete workload.
7. Re-enable scheduled execution only after validation.

Do not delete manifests or existing outputs during an upgrade unless a documented migration explicitly requires it.

## 14. Troubleshooting

### Python version rejected

Use Python 3.11–3.13 and recreate the virtual environment if necessary.

### FFmpeg unavailable

Run `python main.py doctor`, verify the configured `FFMPEG_BIN`, and ensure the selected FFmpeg executable is accessible to the same user that runs the process.

### Translation provider failures

Verify provider credentials, network access, provider quotas, and the configured fallback chain. Do not interpret a successful application start as proof that a translation provider is usable.

### TTS model not found

Check `TTS_MODEL_PATH` and `TTS_VOICES_PATH`, verify both files exist and are readable, and install the `[tts]` extra.

### Scheduled task works manually but fails unattended

Check the working directory, absolute paths, environment loading, credentials, permissions, model paths, FFmpeg availability, and logs. Scheduled execution must not depend on an interactive shell.

### Existing results are being regenerated

Check resume settings, manifests, artifact validation, naming normalization, and whether the result is actually valid. Avoid disabling resume unless a deliberate full reprocesing is required.

## 15. Related documentation

- `README.md` — project overview and quick start.
- `docs/PROJECT_GUIDE.md` — functional and operational overview.
- `docs/TTS.md` — synchronized TTS.
- `docs/TRANSLATION_PROVIDERS.md` — translation providers.
- `docs/UNATTENDED.md` — scheduled execution.
- `docs/DEDUPLICATION.md` — duplicate detection and cleanup.
- `docs/SECURITY.md` — security guidance.
- `docs/AUDIT.md` — audit findings and limitations.
- `docs/RELEASES.md` — release policy.
