# Translation

Translation operates on validated subtitle cues. The provider layer supports a primary provider, fallback providers, retries, delay/backoff and bounded concurrency/batching. A local provider is available for offline processing.

The default configuration is:

```text
primary: Mistral
fallback: Local CTranslate2 → DeepL → MyMemory
batch size: 25
retries: 3
```

The bundled local model currently provides Spanish→English translation. It is an INT8 CTranslate2 conversion of `Helsinki-NLP/opus-mt-es-en`, stored under `tools/models/translation/` after explicit preparation. The selected conversion is pinned to a repository revision and its large model files are SHA-256 verified before use. Its published model license is CC-BY-4.0; attribution must be retained when distributing the model.

## Timing

Translation changes cue text but preserves the original `start`/`end` timestamps. A translated VTT is not considered complete if it is syntactically invalid or contains invalid intervals.

## Recovery

If the original VTT remains valid, translation can be rerun without repeating STT. If STT had to be rebuilt, translation is performed from the newly validated original VTT.

Temporary provider failures are handled by the configured retry/fallback policy. A partial translation must not be represented as a completed artifact.

## Offline local translation

The local provider uses CTranslate2 and SentencePiece and keeps the model loaded for all batches handled by that provider. No Ollama, LM Studio, Google, Azure or remote translation service is required once the model and Python dependencies have been prepared.

Prepare the model explicitly:

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

The download command shows the pinned repository/revision, approximate size, destination, reason and license before requesting confirmation. `--yes` may be used only when the operator explicitly wants non-interactive confirmation. A valid existing model is reused and is never downloaded again.

Cleanup is explicit and only removes the managed local translation model:

```bash
python scripts/manage_local_translation.py cleanup
```

The normal pipeline does not delete source videos, subtitles, outputs, manifests or configuration during this cleanup operation.
