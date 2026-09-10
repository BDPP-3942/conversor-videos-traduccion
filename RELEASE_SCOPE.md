# Release Scope — 1.7.4

## Previous release

`v1.7.2` es la release PATCH inmediatamente anterior publicada. Las correcciones de `1.7.1` y `1.7.2` forman parte del baseline funcional conservado.

Los tags publicados históricos MUST NOT be moved, deleted, or reused.

## Changes since v1.7.2

`1.7.4` es una PATCH de mantenimiento que consolida las correcciones del modelo local y la migración reproducible de desarrollo/CI/build a `uv`.

### Local translation fixes

- `shared_vocabulary.json` puede utilizar una raíz JSON array, que es la estructura real del artefacto fijado.
- Se mantiene el bootstrap empaquetado de `config.json` y `tokenizer_config.json` introducido en la corrección anterior.
- Las regresiones cubren validación, preparación e integración del proveedor local.

### uv migration

- `pyproject.toml` es la única declaración de dependencias Python.
- `uv.lock` queda versionado como resolución reproducible.
- Los entornos de desarrollo, tests, packaging y auditoría se crean mediante `uv sync --locked`.
- Quality, tests y Release Gate utilizan comandos nativos de `uv` para comprobar el entorno.
- `pip-audit` pertenece al grupo `audit` y se ejecuta mediante `uv run --locked --group audit pip-audit --strict`.
- El wheel continúa instalándose mediante `pip` en un entorno limpio como prueba explícita de compatibilidad de distribución.
- La excepción de runtime CUDA conserva el fallback `pip` para ejecutables portables que no contienen `uv`.

## Dependency scope

The runtime dependency contract remains unchanged. Python dependency declarations are maintained only in `pyproject.toml`; the resolved development graph is managed by the versioned `uv.lock` file.

Runtime dependencies:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`
- `webvtt-py>=0.4,<1`
- `imageio-ffmpeg>=0.6,<1`
- `python-dotenv>=1,<2`

Optional project features are declared as PEP 621 extras/groups in `pyproject.toml`. The duplicated `requirements.txt`, `requirements-dev.txt` and `requirements-google.txt` files are no longer dependency sources.

## Version scope

- `pyproject.toml` declares `1.7.4`.
- `config/app.toml` identifies the candidate as `1.7.4`.
- `CHANGELOG.md` contains the `1.7.4` release entry before `1.7.3`.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.7.4` as the candidate.
- The `v1.7.4` tag must point to the exact resulting `main` SHA after merge and final validation.

## Validation state

The final candidate SHA must complete CI and Release Gate successfully before merge approval. No older SHA is sufficient evidence for the final candidate.

## Tests and hardening

- Full pytest suite remains mandatory on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13.
- Ruff lint, Ruff Security, format and `compileall` remain mandatory.
- `uv lock --check`, locked environment sync and dependency consistency are mandatory.
- Packaging, clean-wheel installation, `pip check` and console entry points remain mandatory.
- Dependency audits cover the base/Google development graph and the optional TTS graph using the locked audit group.
- Release Gate validates exact SHA, version metadata, packaged resources and clean-wheel compatibility.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
