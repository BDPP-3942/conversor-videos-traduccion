# Translation

Translation operates on validated subtitle cues. The provider layer supports a primary provider, fallback providers, retries, delay/backoff and concurrency/batch controls.

The current default configuration is:

```text
primary: Mistral
fallback: DeepL → MyMemory
batch size: 25
retries: 3
```

Credentials are provider-specific and must be supplied through the supported environment/profile configuration. See [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md) for provider-specific details.

## Timing

Translation changes cue text but preserves the original `start`/`end` timestamps. A translated VTT is not considered complete if it is syntactically invalid or contains invalid intervals.

## Recovery

If the original VTT remains valid, translation can be rerun without repeating STT. If STT had to be rebuilt, translation is performed from the newly validated original VTT.

Temporary provider failures are handled by the configured retry/fallback policy. A partial translation must not be represented as a completed artifact.
