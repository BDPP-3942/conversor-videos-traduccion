# Packaging

The project provides PyInstaller-based portable builds for Windows and Linux through repository scripts.

## Build dependencies

```bash
python -m pip install -e ".[package]"
```

The package extra provides PyInstaller. The normal Python installation also contains the pinned CTranslate2/SentencePiece runtime required by the local translation provider.

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

## External model resources

Whisper, TTS and local translation model files are external runtime resources and are not embedded into the Python wheel or PyInstaller artifact by default. The local translation model is managed under:

```text
tools/models/translation/opus-mt-es-en-ct2-int8/
```

The model is identified by repository and immutable revision and is validated before loading. Its declared license is CC-BY-4.0, so distribution must preserve attribution. The packaged application must not silently bundle or download the model merely because it was built.

## CUDA

CUDA is optional and must not become a packaging prerequisite for CPU builds. CTranslate2 GPU support depends on the wheel/runtime combination and is validated at runtime. Do not package a machine-specific CUDA installation into the application artifact.

## Validation

Build on the target operating system; do not assume a Windows executable can be produced or validated from Linux/macOS. For a release artifact, install the generated wheel into a clean environment, run `pip check`, exercise every entry point and validate the packaged resource paths. GPU-specific validation belongs to a separately prepared GPU environment.

Build output is created under `dist/VideoTranslationPipeline/` and includes the executable plus runtime configuration/storage/tool directories. Large model files remain external runtime resources.
