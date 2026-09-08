# Release Scope — 1.7.3

## Previous release

`v1.7.2` es la release PATCH inmediatamente anterior y contiene la corrección del gestor de descarga del modelo de traducción local.

Los tags publicados históricos MUST NOT be moved, deleted, or reused.

## Changes since v1.7.2

`1.7.3` es una PATCH que corrige una consideración de packaging/runtime: `config.json` y `tokenizer_config.json` son metadatos necesarios para que CTranslate2 pueda abrir correctamente el modelo local preparado.

Estos dos JSON, fijados por la misma revisión del modelo, pasan a distribuirse con el paquete Python y se copian al directorio gestionado durante la preparación. `shared_vocabulary.json`, que es un artefacto de mayor tamaño del modelo, continúa descargándose desde la revisión fijada y validándose antes de activar el modelo.

## Functional scope

- Garantizar que `config.json` y `tokenizer_config.json` estén disponibles sin depender de una descarga independiente de Hugging Face.
- Instalar los metadatos empaquetados junto a `model.bin` antes de validar el modelo.
- Mantener la descarga y validación de `shared_vocabulary.json`, `model.bin`, `source.spm` y `target.spm`.
- Verificar mediante tests el flujo completo de preparación hasta un modelo utilizable por el proveedor.
- Verificar mediante tests que un modelo preparado puede inicializar CTranslate2 + SentencePiece y ejecutar una traducción.
- Mantener el benchmark real como validación del modelo completo en hardware objetivo.
- Mantener intactas las correcciones de `1.7.1` y `1.7.2`.

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

- `pyproject.toml` declares `1.7.3`.
- `config/app.toml` identifies the candidate as `1.7.3`.
- `CHANGELOG.md` must contain the `1.7.3` release entry before `1.7.2`.
- `docs/RELEASES.md`, `docs/VERSIONING.md`, `RELEASE_CANDIDATE.md` and this file identify `1.7.3` as the candidate.
- The `v1.7.3` tag must point to the exact resulting `main` SHA after merge and final validation.

## Validation state

The final candidate SHA must complete CI and Release Gate successfully before merge approval. No older SHA is sufficient evidence for the final candidate.

The real model benchmark should be executed on the target macOS environment after download to validate the actual CTranslate2 + SentencePiece runtime; deterministic CI tests do not substitute for that hardware validation.

## Tests and hardening

- Bundled metadata regression verifies both packaged JSON resources.
- Download regression verifies that the two bundled JSON files are not fetched remotely and that `shared_vocabulary.json` remains a managed downloaded artifact.
- Provider regression covers initialization from the prepared model directory and a provider translation call through the mocked CTranslate2/SentencePiece boundary.
- Existing STT selective-recovery regressions remain mandatory.
- Existing reprocessing/manifests, Unicode/filesystem, ZIP security, configuration, packaging and dependency checks remain part of the release baseline.

## Excluded

- No replacement media pipeline.
- No alternative storage implementation.
- No arbitrary model/revision download support.
- No automatic global CUDA Toolkit or NVIDIA driver installation/removal.
- No unrelated product feature or broad refactor.
- No release tag creation from the PR branch.
