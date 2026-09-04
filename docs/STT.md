# Speech-to-text (STT)

STT uses `faster-whisper` backed by CTranslate2. The selected model, device, compute type, beam size, CPU threads, VAD behavior, initial prompt and degeneration-recovery policy are configurable.

Defaults in `config/app.toml` include automatic model/device/compute selection, beam size `5`, VAD enabled and a minimum silence duration of `1500` ms. `.env.example` exposes explicit environment overrides.

## Initial prompt / context file

`processing.whisper_initial_prompt` accepts the original literal prompt form and can now also point to a context file.

Supported formats are:

- `.txt`
- `.md`
- `.csv` — cells are flattened into a comma-separated prompt
- `.docx` — paragraph text is extracted from `word/document.xml` without adding a runtime `python-docx` dependency

The repository configuration uses:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

The conventional names `palabras_contexto.txt`, `palabras_contexto.md`, `palabras_contexto.csv` and `palabras_contexto.docx` are also auto-discovered when the configured value is empty. Context files are bounded to 2 MiB and DOCX XML containing DTD/entity declarations is rejected.

For example:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

or, for a literal prompt:

```toml
whisper_initial_prompt = "Tai Chi, taijiquan, qigong"
```

## STT degeneration detection and recovery

The normal transcription path keeps `whisper_condition_on_previous_text` as configured. A segment is considered suspicious when the quality policy detects degeneration signals such as excessive repetition, compression ratio, low average log probability or high no-speech probability. Short legitimate repetition is protected by `whisper_min_repetition_words`.

Suspicious segments are recovered selectively; normal segments are not retranscribed. Recovery is segment-scoped through `clip_timestamps`, so a failure in one interval does not cause the complete media file to be regenerated.

### `whisper_recovery_retries`

`whisper_recovery_retries` is the **maximum number of recovery rounds per suspicious segment**. It is not an unlimited retry loop and it is independent of the initial transcription attempt.

- `0`: disables recovery. A suspicious segment is rejected instead of being retried.
- `1`: performs at most one recovery round.
- `N > 1`: performs at most `N` recovery rounds.

Each recovery round follows the same bounded policy:

1. Retry with `condition_on_previous_text=true`, preserving normal context behavior.
2. If that result is still suspicious or empty, retry the same interval with `condition_on_previous_text=false` to remove prior-text context as a possible source of degeneration.
3. If a healthy candidate is produced, recovery stops immediately; later rounds are not executed.

Therefore, one configured recovery round can make up to **two backend `transcribe` calls** (context-preserving plus context-free). The configuration value counts recovery rounds, not individual backend calls.

`whisper_recovery_temperatures` supplies the temperature used by each recovery round. If fewer temperatures than rounds are configured, values are reused cyclically. If the list is empty, recovery uses `0.0`.

All candidates from the executed rounds are scored using the same STT quality policy. The best candidate is selected, but it is emitted only if it is no longer suspicious. A candidate that remains suspicious after all configured rounds is rejected; the pipeline does not silently accept a known-degenerate transcription.

Recovery logs include the interval, configured retry count, candidate count and quality metrics/reasons, but do not log the recovered transcription text.

Configuration example:

```toml
whisper_recovery_retries = 1
whisper_recovery_temperatures = [0.2]
```

Environment overrides:

```text
WHISPER_RECOVERY_RETRIES=1
WHISPER_RECOVERY_TEMPERATURES=0.2,0.4
```

This policy deliberately bounds recovery work and makes `whisper_recovery_retries` observable and testable. The tests verify disabled recovery, the retry limit, temperature selection, context-preserving/context-free ordering and early termination after a healthy candidate.

The recovery mechanism is a defensive STT policy, not a guarantee that every hallucination can be corrected. Real-media regression claims require an actual representative media fixture or recorded execution; synthetic tests do not constitute an A/B benchmark.

## Hardware and GPU/CPU execution

Hardware detection verifies the actual CTranslate2 CUDA capability instead of treating the presence of a GPU driver as sufficient. The effective profile records CPU count, available RAM, GPU/VRAM, selected model, device and compute type.

When CUDA is selected, the Whisper model executes on the GPU. CPU resources are still used by the surrounding Python/media pipeline, but `cpu_threads` must not be interpreted as a mechanism for splitting one Whisper inference between CPU and GPU. The project therefore does **not** claim single-inference CPU+GPU model partitioning.

The supported throughput strategy is parallelism between independent video jobs when the resource budget permits it. Each video worker owns its Whisper instance (`num_workers=1` inside that instance), while the pipeline-level concurrency ceiling accounts for CPU threads, available RAM and GPU memory. This avoids duplicating work or creating uncontrolled concurrent generation inside a single model instance.

The upstream `faster-whisper` API exposes explicit `device`, `compute_type`, `cpu_threads` and `num_workers` controls. Its documented GPU examples select `device="cuda"`; CPU execution selects `device="cpu"`. The project follows that backend contract rather than inventing an unsupported hybrid inference mode.

If CUDA initialization fails, the application performs one controlled fallback to CPU rather than repeatedly retrying the same failed GPU initialization.

## Segmentation

Whisper timestamps are used to construct subtitle cues. The pipeline can split cues around significant detected silences. Final intervals are validated before a VTT is accepted.

The invariant is:

```text
start < end
```

Cues violating the invariant are not propagated as usable subtitles.

## Model prefetch

To initialize/download the automatically selected model:

```bash
python main.py prefetch-whisper
```

The model is not bundled into the repository by default.

## Reprocessing

If an existing original VTT is missing or invalid but the normal video exists, `reprocess-subtitles --stt-only` can regenerate the transcription without regenerating the normal video.
