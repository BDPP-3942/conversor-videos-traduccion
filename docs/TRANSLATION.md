# Translation

Translation operates on validated subtitle cues. The provider layer supports a primary provider, fallback providers, retries, delay/backoff and concurrency/batch controls.

The current default configuration is:

```text
primary: Mistral
fallback: Local CTranslate2 → DeepL → MyMemory
batch size: 25
retries: 3
```

The local provider is the first fallback. It can continue translation without a remote provider when the pinned model has been prepared locally. If the local resource is unavailable or cannot be initialized because of a resource/runtime failure, the configured chain can continue with DeepL and MyMemory. An invalid provider configuration is not silently converted into another provider.

Credentials are provider-specific and must be supplied through the supported environment/profile configuration. The local provider uses `LOCAL_TRANSLATION_*` and does not require API credentials. See [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md) and [LOCAL_TRANSLATION.md](LOCAL_TRANSLATION.md) for provider-specific details.

## Timing

Translation changes cue text but preserves the original `start`/`end` timestamps. A translated VTT is not considered complete if it is syntactically invalid or contains invalid intervals.

## Recovery

If the original VTT remains valid, translation can be rerun without repeating STT. If STT had to be rebuilt, translation is performed from the newly validated original VTT.

Temporary provider failures are handled by the configured retry/fallback policy. A partial translation must not be represented as a completed artifact.
