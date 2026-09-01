# Speech-to-text (STT)

STT uses `faster-whisper` backed by CTranslate2. The selected model, device, compute type, beam size, CPU threads, VAD behavior and initial prompt are configurable.

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
