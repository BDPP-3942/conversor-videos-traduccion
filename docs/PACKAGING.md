# Packaging

The project provides PyInstaller-based portable builds for Windows and Linux through repository scripts. There is currently no repository packaging script for macOS.

## Build dependencies

Build tooling is declared in the `dev` uv dependency group and the TTS runtime is enabled explicitly because the packaged executable collects the TTS runtime:

```bash
uv sync --group dev --extra tts
```

There is no `[package]` extra in `pyproject.toml`; packaging dependencies are managed through the uv `dev` group.

## Windows

```bat
scripts\build_windows.bat
```

Use `--no-webm` to disable the secondary WebM output in the packaged configuration when the build script exposes that option.

## Linux

```bash
./scripts/build_linux.sh
```

Use `--no-webm` for the same configuration change when supported by the build script.

Build output is created under `dist/VideoTranslationPipeline/` and includes the executable plus runtime configuration/storage/tool directories. Whisper, local-translation and TTS model files are external runtime resources and are not embedded by these scripts.

Build on the target operating system; do not assume a Windows executable can be produced or validated from Linux/macOS, or that a Linux build is portable to another operating system.

The packaged artifact is validated in CI by building with `uv build`/the repository packaging flow, installing the resulting wheel into a clean environment with `pip`, running `pip check` and exercising the installed console entry points. The portable PyInstaller build is an additional platform-specific distribution mechanism.

## Release 1.8.0

The published `1.8.0` release retains the Windows/Linux packaging scope above. It does not introduce a macOS PyInstaller build. Local model resources remain external and must be prepared separately when the local translation provider is enabled.
