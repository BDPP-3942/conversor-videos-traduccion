# Speech-to-text (STT)

STT uses `faster-whisper` backed by CTranslate2. PR2 controls the compatible runtime versions explicitly instead of depending on `latest`:

```text
Python: >=3.11,<3.14
faster-whisper: >=1.2.1,<1.3
CTranslate2: >=4.8.2,<4.9
```

The selected model, device, compute type, beam size, CPU threads, VAD behavior and initial prompt are configurable.

Defaults in `config/app.toml` include automatic model/device/compute selection, beam size `5`, VAD enabled and a minimum silence duration of `1500` ms. `.env.example` exposes explicit environment overrides.

## Initial prompt / context file

`processing.whisper_initial_prompt` accepts the original literal prompt form and can also point to a context file.

Supported formats are `.txt`, `.md`, `.csv` and `.docx`. Context files are bounded to 2 MiB and DOCX XML containing DTD/entity declarations is rejected.

## Hardware and GPU/CPU execution

Hardware detection verifies the actual CTranslate2 CUDA capability instead of treating the presence of a GPU driver as sufficient. The effective profile records CPU count, available RAM, GPU/VRAM, selected model, device and compute type.

The supported execution path is:

```text
NVIDIA GPU
   ↓
driver
   ↓
CUDA runtime/dependencies required by the selected CTranslate2 wheel
   ↓
CTranslate2 CUDA probe
   ↓
faster-whisper
   ↓
Whisper pipeline
```

The application does not install the complete CUDA Toolkit merely to detect a GPU. Runtime components must be compatible with the selected CTranslate2 build. The exact installed runtime is environment-dependent and remains `NO VERIFICADO` until `doctor`/runtime probes confirm it on the host.

When CUDA is selected, the Whisper model executes on the GPU. CPU resources are still used by the surrounding Python/media pipeline, but `cpu_threads` must not be interpreted as a mechanism for splitting one Whisper inference between CPU and GPU. The project therefore does **not** claim single-inference CPU+GPU model partitioning.

The supported throughput strategy is parallelism between independent video jobs when the resource budget permits it. Each video worker owns its Whisper instance (`num_workers=1` inside that instance), while the pipeline-level concurrency ceiling accounts for CPU threads, available RAM and GPU memory.

If CUDA initialization fails, the application performs one controlled fallback to CPU with `int8`. It does not leave the pipeline in a partially initialized GPU state.

AMD/ROCm and other GPU vendors may be detected as hardware, but they are not considered Whisper GPU backends unless the complete CTranslate2/faster-whisper path has been positively verified. Therefore detection of an AMD/ROCm GPU alone does not force an unsupported CUDA backend.

## Model prefetch

To initialize/download the automatically selected Whisper model:

```bash
python main.py prefetch-whisper
```

Whisper weights are not bundled into the repository by default.

## Segmentation

Whisper timestamps are used to construct subtitle cues. The pipeline can split cues around significant detected silences. Final intervals are validated before a VTT is accepted.

The invariant is:

```text
start < end
```

Cues violating the invariant are not propagated as usable subtitles.

## Reprocessing

If an existing original VTT is missing or invalid but the normal video exists, `reprocess-subtitles --stt-only` can regenerate the transcription without regenerating the normal video.
