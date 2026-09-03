# Packaging

The project provides PyInstaller-based portable builds for Windows and Linux through repository scripts.

## Build dependencies

```bash
python -m pip install -e ".[package]"
```

The package extra provides PyInstaller. The build scripts additionally install development and TTS dependencies because the generated executable collects the TTS runtime.

## Windows

```bat
scripts\build_windows.bat
```

Use `--no-webm` to disable the secondary WebM output in the packaged configuration.

## Linux

```bash
./scripts/build_linux.sh
```

Use `--no-webm` for the same configuration change.

Build output is created under `dist/VideoTranslationPipeline/` and includes the executable plus runtime configuration/storage/tool directories. Whisper and TTS model files are external runtime resources and are not embedded by these scripts.

Build on the target operating system; do not assume a Windows executable can be produced or validated from Linux/macOS.
