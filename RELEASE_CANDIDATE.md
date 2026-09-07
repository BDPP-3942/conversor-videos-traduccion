# Release Candidate — 1.6.1

## Release

- **Version:** 1.6.1
- **Candidate SHA:** debe ser validado por CI y Release Gate sobre el SHA exacto final pre-merge; el tag debe apuntar al SHA exacto resultante de `main` tras el merge.
- **Previous release:** `v1.5.1` → `06ee8d265b57214596f079f3bb426b9b27042b1e`
- **Prior candidate:** `1.6.0` — no se crea desde esta rama de corrección.
- **Target tag:** `v1.6.1` — not created

This report is the release-gate record for the faster-whisper selective-recovery compatibility fix. The tag must be created only after merge, must point to the exact final `main` commit and must never be moved afterward.

## Scope

- Corrección del contrato de `clip_timestamps` usado por la recuperación selectiva de `faster-whisper`.
- Los intervalos se envían como valores temporales numéricos `[start, end]` a `WhisperModel.transcribe()`.
- Conservación de la recuperación limitada por segmento, el contexto preservado/contexto libre y la parada temprana ante candidatos saludables.
- Sin sustitución del pipeline audiovisual, almacenamiento, naming, VTT ni contratos públicos de recuperación.
- El endurecimiento ZIP/filesystem, la traducción local opcional y el runtime GPU de `1.6.0` permanecen como baseline funcional del proyecto.

## Root cause

La recuperación selectiva construía `clip_timestamps` como diccionarios de segmento. El flujo utilizado por el proyecto llama directamente a `WhisperModel.transcribe()`, cuyo contrato espera timestamps numéricos. `faster-whisper` realiza operaciones aritméticas sobre esos valores durante el procesamiento del clip; recibir un diccionario provoca `TypeError: unsupported operand type(s) for *: 'dict' and 'int'`.

La corrección convierte el intervalo recuperado en `[float(start), float(end)]` antes de invocar `transcribe()`.

## Dependencies

The release stack is explicitly constrained to the compatible versions:

- `faster-whisper>=1.2.1,<1.3`
- `ctranslate2>=4.8.2,<4.9`
- `sentencepiece>=0.2,<0.3`
- `huggingface-hub>=0.32,<1.31`

`pyproject.toml` and `requirements.txt` use the same runtime constraints. `requirements-google.txt` and `requirements-dev.txt` inherit from `requirements.txt` rather than duplicating the `faster-whisper` constraint.

## Tests

Required validation includes the complete pytest suite, STT recovery regressions, configuration/provider regressions, ZIP/filesystem security tests, packaging validation and dependency audits.

The STT regressions verify the numeric `clip_timestamps` contract received by `model.transcribe()`, normal transcription, recovery result integration, bounded retry behavior and early termination after a healthy candidate.

## CI

CI validates the exact PR head on Linux, Windows and macOS with Python 3.11, 3.12 and 3.13, plus project-wide Ruff lint/security/format checks, compile checks, dependency audits, packaging, clean-wheel installation, `pip check` and entry points. Release Gate validates the candidate SHA, version metadata, distribution build and clean installation.

**Current validation status:** PENDING until the final candidate SHA completes the authoritative CI and Release Gate checks.

## Packaging

`pyproject.toml` declares `1.6.1`.

Supported packaged entry points are:

- `video-translation-pipeline`
- `video-translation-regenerate`
- `video-subtitle-qa`
- `video-translation-tts`

`video-translation-scheduled` is not declared and remains unsupported as a standalone entry point; scheduled execution uses `video-translation-pipeline run --scheduled`.

## Documentation

The release documentation for `1.6.1` is maintained in `CHANGELOG.md`, `docs/RELEASES.md`, `RELEASE_SCOPE.md`, this report and the STT/installation documentation. Historical release entries must remain intact and must not be deleted when adding the new candidate.

## Known limitations

- Real GPU benchmark performance is hardware-dependent and is not a release requirement unless explicitly executed and recorded.
- Google Drive and rclone production credentials remain outside deterministic CI.
- Full external TTS provider execution is not a mandatory networked CI dependency.
- CI validates the local translation provider with deterministic test doubles; it does not download and execute the full model on every runner.
- No real-media A/B claim is made without an actual recorded fixture/execution.

## Release Gate

| Gate | Status |
|---|---|
| Existing functionality | **PENDING final CI** |
| STT selective recovery compatibility | **IMPLEMENTED** |
| faster-whisper dependency contract | **IMPLEMENTED** |
| Tests | **PENDING final CI** |
| CI | **PENDING** |
| Packaging | **PENDING final CI** |
| Documentation | **UPDATED** |
| Versioning | **UPDATED to 1.6.1** |

## Decision

**Do not merge or create `v1.6.1` until the final pre-merge SHA remains green in CI and Release Gate.** After merge, validate the resulting `main` SHA and create the immutable `v1.6.1` tag/release on that exact SHA.
