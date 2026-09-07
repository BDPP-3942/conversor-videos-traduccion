# Release Scope — 1.7.2

## Previous release

`v1.7.1` es la release PATCH inmediatamente anterior en el historial de producto y corresponde al estado de `main` que corrigió la recuperación selectiva STT; su tag/release debe apuntar al SHA exacto del merge ya validado.

El tag `v1.7.0` es histórico y MUST NOT be moved, deleted, or reused.

## Historical baselines

`v1.7.0` → `036a9a4cf33012d0fcd0a784f8ff34db6e30b0f5`.

`v1.6.0` → `a6cf0ee183a4802814fe0e061b4704e427166b85`.

`v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`.

## Changes since v1.7.1

`1.7.2` es una PATCH que corrige el gestor de descarga del modelo de traducción local. La expresión que calculaba el límite de descarga evaluaba de forma eager el fallback de `dict.get`, provocando `KeyError: 'model.bin'` al procesar precisamente uno de los ficheros principales definidos en `MODEL_FILES`.

La corrección selecciona explícitamente el límite según el tipo de fichero y añade regresiones para el flujo completo de preparación y carga del proveedor local.

## Functional scope

- Corregir la descarga del modelo local fijado sin `KeyError` en `model.bin`.
- Mantener la validación por tamaño, SHA-256 y metadatos JSON.
- Verificar mediante tests el flujo completo de descarga gestionada hasta un modelo utilizable por el proveedor.
- Verificar mediante tests que un modelo preparado puede inicializar CTranslate2 + SentencePiece y ejecutar una traducción.
- Mantener el benchmark real como validación del modelo completo en hardware objetivo.
- Mantener intacta la corrección de recuperación selectiva STT introducida en `1.7.1`.

## Dependency scope

The runtime dependency contract remains unchanged:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`
- `webvtt-py>=0.4,<1`
- `imageio-ffmpeg>=0.6,<1`
- `python-dotenv>=1,<2`

`requirements.txt` and `pyproject.toml` must remain aligned.

## Configuration scope

No new public configuration key is required. The existing `LOCAL_TRANSLATION_*` environment configuration and pinned model/revision contract remain unchanged.

## Version scope

- `pyproject.toml` declares `1.7.2`.
- `config/app.toml` identifies the candidate as `1.7.2`.
- `CHANGELOG.md` must contain the `1.7.2` release entry before `1.7.1`.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.7.2` as the candidate.
- The `v1.7.2` tag must point to the exact resulting `main` SHA after merge and final validation.

## Validation state

The final candidate SHA must complete CI and Release Gate successfully before merge approval. No older SHA is sufficient evidence for the final candidate.

The real model benchmark should be executed on the target macOS environment after download to validate the actual CTranslate2 + SentencePiece runtime; deterministic CI tests do not substitute for that hardware validation.

## Tests and hardening

- Download regression covers every managed model file, including `model.bin` and all metadata.
- Provider regression covers initialization from the downloaded model directory and a real provider call through the mocked CTranslate2/SentencePiece boundary.
- Existing STT selective-recovery regressions remain mandatory.
- Existing reprocessing/manifests, Unicode/filesystem, ZIP security, configuration, packaging and dependency checks remain part of the release baseline.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
