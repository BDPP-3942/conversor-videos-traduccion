from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config.settings import BASE_DIR
from src.application import ApplicationError, VideoTranslationApplication
from src.runtime_paths import ensure_runtime_storage, runtime_storage_paths


class Worker:
    def __init__(self, task, report) -> None:
        self.task = task
        self.report = report
        self.thread: threading.Thread | None = None
        self.cancel_event = threading.Event()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, name="pipeline-worker", daemon=True)
        self.thread.start()

    def cancel(self) -> None:
        self.cancel_event.set()

    def _run(self) -> None:
        try:
            result = self.task(self.report, self.cancel_event)
            self.report({"stage": "finished", "message": json.dumps(result, ensure_ascii=False, indent=2)})
        except ApplicationError as exc:
            self.report({"stage": "error", "message": str(exc)})
        except Exception as exc:
            self.report({"stage": "error", "message": f"Unexpected error: {type(exc).__name__}: {exc}"})


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Video Translation Pipeline")
        self.root.geometry("1120x860")
        self.root.minsize(960, 720)
        self.worker: Worker | None = None
        self.runtime = ensure_runtime_storage()
        try:
            self.settings = VideoTranslationApplication().load_settings()
        except Exception:
            self.settings = None
        self._build()

    def _setting(self, name: str, default):
        return getattr(self.settings, name, default) if self.settings is not None else default

    def _build(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)
        processing = ttk.Frame(notebook, padding=12)
        recovery = ttk.Frame(notebook, padding=12)
        duplicates = ttk.Frame(notebook, padding=12)
        diagnostics = ttk.Frame(notebook, padding=12)
        scheduling = ttk.Frame(notebook, padding=12)
        notebook.add(processing, text="Process")
        notebook.add(recovery, text="Subtitle recovery")
        notebook.add(duplicates, text="Duplicates")
        notebook.add(diagnostics, text="Diagnostics")
        notebook.add(scheduling, text="CLI & scheduling")
        self._build_processing(processing)
        self._build_recovery(recovery)
        self._build_duplicates(duplicates)
        self._build_diagnostics(diagnostics)
        self._build_scheduling(scheduling)

        status_bar = ttk.Frame(container)
        status_bar.pack(fill="x", pady=(8, 0))
        self.status = tk.StringVar(value="Ready")
        ttk.Label(status_bar, textvariable=self.status).pack(side="left")
        self.progress = ttk.Progressbar(status_bar, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True, padx=12)
        self.cancel = ttk.Button(status_bar, text="Cancel", command=self.cancel_processing, state="disabled")
        self.cancel.pack(side="right")
        log_frame = ttk.LabelFrame(container, text="Execution log", padding=8)
        log_frame.pack(fill="both", expand=False, pady=(8, 0))
        self.log = tk.Text(log_frame, height=9, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _build_processing(self, parent: ttk.Frame) -> None:
        paths = ttk.LabelFrame(parent, text="Working folders", padding=10)
        paths.pack(fill="x", pady=(0, 10))
        self.provider = tk.StringVar(value="local")
        self.source = tk.StringVar(value=str(self.runtime["input"]))
        self.target = tk.StringVar(value=str(self.runtime["output"]))
        self._combo_row(paths, 0, "Provider", self.provider, ["local", "google_drive", "rclone"])
        self._path_row(paths, 1, "Input folder", self.source, directory=True)
        self._path_row(paths, 2, "Output folder", self.target, directory=True)
        ttk.Label(
            paths,
            text="For packaged desktop builds these folders are user-writable application data. You can select any other folders without administrator rights.",
            wraplength=820,
        ).grid(row=3, column=1, sticky="w", pady=(4, 0))

        general = ttk.LabelFrame(parent, text="Translation", padding=10)
        general.pack(fill="x", pady=(0, 10))
        self.source_lang = tk.StringVar(value=self._setting("source_lang", "es"))
        self.target_lang = tk.StringVar(value=self._setting("target_lang", "en"))
        self.translation = tk.StringVar(value=self._setting("translation_provider", "mistral"))
        self.fallback = tk.StringVar(value=",".join(self._setting("translation_fallback_providers", ("deepl", "mymemory"))))
        self._entry_row(general, 0, "Source language", self.source_lang)
        self._entry_row(general, 1, "Target language", self.target_lang)
        self._combo_row(general, 2, "Translation provider", self.translation, ["mistral", "local", "deepl", "mymemory"])
        self._entry_row(general, 3, "Fallback providers", self.fallback)
        self.local_model = tk.StringVar(value=self._setting("local_translation_model", "madlad400-3b-ct2-int8"))
        self.local_device = tk.StringVar(value=self._setting("local_translation_device", "auto"))
        self.local_compute = tk.StringVar(value=self._setting("local_translation_compute_type", "auto"))
        self.local_beam = tk.IntVar(value=self._setting("local_translation_beam_size", 2))
        self._entry_row(general, 4, "Local model", self.local_model)
        self._combo_row(general, 5, "Local device", self.local_device, ["auto", "cpu", "cuda"])
        self._entry_row(general, 6, "Local compute type", self.local_compute)
        self._spin_row(general, 7, "Local beam size", self.local_beam, 1, 16)

        execution = ttk.LabelFrame(parent, text="Execution", padding=10)
        execution.pack(fill="x", pady=(0, 10))
        self.parallel = tk.IntVar(value=self._setting("max_parallel_videos", 0))
        self.batch_size = tk.IntVar(value=self._setting("translation_batch_size", 25))
        self.webm = tk.BooleanVar(value=self._setting("generate_webm", False))
        self.tts = tk.BooleanVar(value=self._setting("tts_enabled", False))
        self.tts_required = tk.BooleanVar(value=self._setting("tts_required", False))
        self.resume = tk.BooleanVar(value=self._setting("resume_enabled", True))
        self.normalize_names = tk.BooleanVar(value=self._setting("normalize_legacy_names", True))
        self.auto_dedupe = tk.BooleanVar(value=self._setting("automatic_output_deduplication", False))
        self._spin_row(execution, 0, "Parallel videos (0 = AUTO)", self.parallel, 0, 64)
        self._spin_row(execution, 1, "Translation batch size", self.batch_size, 1, 500)
        self._check_row(execution, 2, "Generate secondary WebM", self.webm)
        self._check_row(execution, 3, "Enable synchronized TTS", self.tts)
        self._check_row(execution, 4, "TTS required for success", self.tts_required)
        self._check_row(execution, 5, "Resume compatible results", self.resume)
        self._check_row(execution, 6, "Normalize legacy output names", self.normalize_names)
        self._check_row(execution, 7, "Automatic output deduplication", self.auto_dedupe)

        advanced = ttk.LabelFrame(parent, text="STT / media / context", padding=10)
        advanced.pack(fill="x", pady=(0, 10))
        self.whisper_model = tk.StringVar(value=self._setting("whisper_model", "auto"))
        self.whisper_device = tk.StringVar(value=self._setting("whisper_device", "auto"))
        self.whisper_compute = tk.StringVar(value=self._setting("whisper_compute_type", "auto"))
        self.whisper_beam = tk.IntVar(value=self._setting("whisper_beam_size", 5))
        self.whisper_vad = tk.BooleanVar(value=self._setting("whisper_vad_filter", True))
        self.whisper_silence = tk.IntVar(value=self._setting("whisper_min_silence_duration_ms", 2000))
        self.whisper_split = tk.IntVar(value=self._setting("whisper_subtitle_split_silence_duration_ms", 1000))
        self.context = tk.StringVar(value=self._setting("whisper_initial_prompt", ""))
        self.ffmpeg_preset = tk.StringVar(value=self._setting("ffmpeg_preset", "medium"))
        self.ffmpeg_crf = tk.IntVar(value=self._setting("ffmpeg_crf", 23))
        self.ffmpeg_bitrate = tk.StringVar(value=self._setting("ffmpeg_audio_bitrate", "256k"))
        self._entry_row(advanced, 0, "Whisper model", self.whisper_model)
        self._combo_row(advanced, 1, "Whisper device", self.whisper_device, ["auto", "cpu", "cuda"])
        self._entry_row(advanced, 2, "Whisper compute type", self.whisper_compute)
        self._spin_row(advanced, 3, "Whisper beam size", self.whisper_beam, 1, 32)
        self._check_row(advanced, 4, "Whisper VAD filter", self.whisper_vad)
        self._spin_row(advanced, 5, "Minimum silence (ms)", self.whisper_silence, 0, 10000)
        self._spin_row(advanced, 6, "Subtitle split silence (ms)", self.whisper_split, 0, 10000)
        self._file_row(advanced, 7, "Context words file / prompt", self.context)
        self._entry_row(advanced, 8, "FFmpeg preset", self.ffmpeg_preset)
        self._spin_row(advanced, 9, "FFmpeg CRF", self.ffmpeg_crf, 0, 51)
        self._entry_row(advanced, 10, "FFmpeg audio bitrate", self.ffmpeg_bitrate)
        self.tts_voice = tk.StringVar(value=self._setting("tts_voice", "am_michael"))
        self.tts_speed = tk.DoubleVar(value=self._setting("tts_speed", 1.0))
        self._entry_row(advanced, 11, "Kokoro TTS voice", self.tts_voice)
        ttk.Label(advanced, text="TTS speed (0.50–1.35x)").grid(row=12, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(advanced, from_=0.5, to=1.35, increment=0.05, textvariable=self.tts_speed, width=12).grid(row=12, column=1, sticky="w", pady=4)
        advanced.columnconfigure(1, weight=1)

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=(4, 0))
        self.start = ttk.Button(buttons, text="▶  Run translation", command=self.start_processing)
        self.start.pack(side="left", ipadx=18, ipady=6)
        ttk.Label(buttons, text="All values above are passed to the existing application/pipeline; no separate GUI implementation of the media logic is used.").pack(side="left", padx=14)

    def _build_recovery(self, parent: ttk.Frame) -> None:
        self.recovery_target = tk.StringVar(value=str(self.runtime["output"]))
        self.recovery_folder = tk.StringVar()
        self.recovery_video = tk.StringVar()
        self.recovery_mode = tk.StringVar(value="full")
        self._path_row(parent, 0, "Output directory", self.recovery_target)
        self._entry_row(parent, 1, "Output folder (optional)", self.recovery_folder)
        self._entry_row(parent, 2, "Video name (optional)", self.recovery_video)
        self._combo_row(parent, 3, "Recovery mode", self.recovery_mode, ["full", "stt_only", "translate_only"])
        ttk.Label(parent, text="Recovery reuses existing audiovisual media and repairs subtitle artefacts.", wraplength=820).grid(row=4, column=0, columnspan=3, sticky="w", pady=10)
        ttk.Button(parent, text="Run subtitle recovery", command=self.start_recovery).grid(row=5, column=0, sticky="w")
        ttk.Button(parent, text="Recover all eligible outputs", command=self.start_recovery_all).grid(row=5, column=1, sticky="w", padx=8)
        parent.columnconfigure(1, weight=1)

    def _build_duplicates(self, parent: ttk.Frame) -> None:
        self.duplicate_target = tk.StringVar(value=str(self.runtime["output"]))
        self._path_row(parent, 0, "Local output directory", self.duplicate_target)
        ttk.Label(parent, text="Scan/analyze are non-destructive. Delete requires confirmation and supports dry-run.", wraplength=820).grid(row=1, column=0, columnspan=3, sticky="w", pady=10)
        buttons = ttk.Frame(parent)
        buttons.grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Button(buttons, text="Scan", command=lambda: self.start_duplicate("scan")).pack(side="left")
        ttk.Button(buttons, text="Analyze", command=lambda: self.start_duplicate("analyze")).pack(side="left", padx=8)
        ttk.Button(buttons, text="Delete dry-run", command=lambda: self.start_duplicate("delete", True)).pack(side="left")
        ttk.Button(buttons, text="Delete duplicates", command=lambda: self.start_duplicate("delete", False)).pack(side="left", padx=8)

    def _build_diagnostics(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Run these checks before processing after changing models, FFmpeg, storage or provider configuration.", wraplength=820).pack(anchor="w", pady=(0, 12))
        buttons = ttk.Frame(parent)
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Run doctor", command=self.start_doctor).pack(side="left")
        ttk.Button(buttons, text="Prefetch Whisper model", command=self.start_prefetch).pack(side="left", padx=8)
        ttk.Button(buttons, text="Open user data folder", command=self.open_runtime_folder).pack(side="left")

    def _build_scheduling(self, parent: ttk.Frame) -> None:
        text = (
            "The desktop GUI is interactive; the existing CLI remains the unattended automation contract.\n\n"
            "Manual: uv run video-translation-pipeline run\n"
            "Scheduled: uv run video-translation-pipeline run --scheduled\n\n"
            "Windows: use the existing .bat/.ps1 wrappers with Task Scheduler.\n"
            "macOS: launchd via scripts/install_launchd.sh\n"
            "Linux/macOS: existing scheduled wrappers."
        )
        ttk.Label(parent, text=text, justify="left", wraplength=850).pack(anchor="w")

    def _path_row(self, parent, row: int, label: str, variable: tk.StringVar, directory: bool = True) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Browse…", command=lambda: self._browse(variable, directory=directory)).grid(row=row, column=2, padx=(8, 0))
        parent.columnconfigure(1, weight=1)

    def _file_row(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Choose file…", command=lambda: self._browse_file(variable)).grid(row=row, column=2, padx=(8, 0))
        ttk.Button(parent, text="Clear", command=lambda: variable.set("")).grid(row=row, column=3, padx=(4, 0))
        parent.columnconfigure(1, weight=1)

    @staticmethod
    def _entry_row(parent, row: int, label: str, variable: tk.Variable) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

    @staticmethod
    def _combo_row(parent, row: int, label: str, variable: tk.Variable, values: list[str]) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=24).grid(row=row, column=1, sticky="w", pady=4)

    @staticmethod
    def _spin_row(parent, row: int, label: str, variable: tk.Variable, minimum: int, maximum: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(parent, from_=minimum, to=maximum, textvariable=variable, width=12).grid(row=row, column=1, sticky="w", pady=4)

    @staticmethod
    def _check_row(parent, row: int, label: str, variable: tk.BooleanVar) -> None:
        ttk.Checkbutton(parent, text=label, variable=variable).grid(row=row, column=1, sticky="w", pady=4)

    @staticmethod
    def _browse(variable: tk.StringVar, directory: bool = True) -> None:
        if directory:
            selected = filedialog.askdirectory(initialdir=variable.get() or str(Path.home()))
        else:
            selected = filedialog.askopenfilename(initialdir=variable.get() or str(Path.home()))
        if selected:
            variable.set(selected)

    @staticmethod
    def _browse_file(variable: tk.StringVar) -> None:
        selected = filedialog.askopenfilename(
            initialdir=str(Path(variable.get()).parent) if variable.get() else str(Path.home()),
            filetypes=[("Context files", "*.txt *.md *.csv *.docx"), ("All files", "*.*")],
        )
        if selected:
            variable.set(selected)

    def _busy(self, busy: bool) -> None:
        self.start.configure(state="disabled" if busy else "normal")
        self.cancel.configure(state="normal" if busy else "disabled")
        if busy:
            self.progress["value"] = 0
        self.status.set("Processing…" if busy else "Ready")

    def _launch(self, task) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            return
        self._busy(True)
        self.worker = Worker(task, self._report)
        self.worker.start()

    def start_processing(self) -> None:
        provider = self.provider.get()
        context = self.context.get().strip()
        options: dict[str, object] = {
            "provider": provider,
            "source_lang": self.source_lang.get().strip(),
            "target_lang": self.target_lang.get().strip(),
            "translation_provider": self.translation.get(),
            "translation_fallback_providers": tuple(x.strip() for x in self.fallback.get().split(",") if x.strip()),
            "max_parallel_videos": self.parallel.get(),
            "translation_batch_size": self.batch_size.get(),
            "generate_webm": self.webm.get(),
            "tts_enabled": self.tts.get(),
            "tts_required": self.tts_required.get(),
            "resume_enabled": self.resume.get(),
            "normalize_legacy_names": self.normalize_names.get(),
            "automatic_output_deduplication": self.auto_dedupe.get(),
            "whisper_model": self.whisper_model.get().strip(),
            "whisper_device": self.whisper_device.get(),
            "whisper_compute_type": self.whisper_compute.get().strip(),
            "whisper_beam_size": self.whisper_beam.get(),
            "whisper_vad_filter": self.whisper_vad.get(),
            "whisper_min_silence_duration_ms": self.whisper_silence.get(),
            "whisper_subtitle_split_silence_duration_ms": self.whisper_split.get(),
            "whisper_initial_prompt": context,
            "ffmpeg_preset": self.ffmpeg_preset.get().strip(),
            "ffmpeg_crf": self.ffmpeg_crf.get(),
            "ffmpeg_audio_bitrate": self.ffmpeg_bitrate.get().strip(),
            "local_translation_model": self.local_model.get().strip(),
            "local_translation_device": self.local_device.get(),
            "local_translation_compute_type": self.local_compute.get().strip(),
            "local_translation_beam_size": self.local_beam.get(),
            "tts_voice": self.tts_voice.get().strip(),
            "tts_speed": self.tts_speed.get(),
        }
        if provider == "local":
            options["source"] = self.source.get().strip()
            options["target"] = self.target.get().strip()
        if not options.get("source") and provider == "local":
            messagebox.showerror("Input folder required", "Select an input folder before running.", parent=self.root)
            return
        self._append("Starting translation in a background worker.\n")
        self._launch(lambda report, cancel: VideoTranslationApplication().run(progress=report, cancel_event=cancel, **options))

    def start_recovery(self) -> None:
        folder = self.recovery_folder.get().strip()
        video = self.recovery_video.get().strip()
        if not folder and not video:
            messagebox.showerror("Recovery target required", "Specify an output folder or a video name.", parent=self.root)
            return
        self._append("Starting subtitle recovery.\n")
        self._launch(lambda _report, _cancel: VideoTranslationApplication().reprocess_subtitles(target=self.recovery_target.get(), mode=self.recovery_mode.get(), output_folder=folder or None, video_name=video or None, provider="local"))

    def start_recovery_all(self) -> None:
        self._append("Starting subtitle recovery for all eligible outputs.\n")
        self._launch(lambda _report, _cancel: VideoTranslationApplication().reprocess_all(target=self.recovery_target.get(), mode=self.recovery_mode.get(), provider="local"))

    def start_duplicate(self, action: str, dry_run: bool = False) -> None:
        if action == "delete" and not dry_run and not messagebox.askyesno("Confirm deletion", "Delete the duplicates in the persisted deletion plan?", parent=self.root):
            return
        self._append(f"Starting duplicate {action}.\n")
        self._launch(lambda _report, _cancel: VideoTranslationApplication.deduplicate(self.duplicate_target.get(), action, dry_run=dry_run))

    def start_doctor(self) -> None:
        self._append("Running runtime doctor.\n")
        self._launch(lambda _report, _cancel: self._doctor())

    def _doctor(self) -> dict[str, object]:
        from src.auth.unattended import check_unattended
        from src.ffmpeg_resolver import FFmpegResolver

        ensure_runtime_storage()
        settings = VideoTranslationApplication().load_settings()
        ffmpeg = FFmpegResolver.doctor(settings)
        readiness = check_unattended(settings, ensure_rclone_binary=False)
        return {"config": self.config_path_exists(), "runtime_storage": str(self.runtime["root"]), "python": True, "ffmpeg": ffmpeg, "unattended_ready": readiness.ready, "provider_checks": readiness.checks, "provider_errors": readiness.errors}

    @staticmethod
    def config_path_exists() -> bool:
        return (BASE_DIR / "config" / "app.toml").is_file()

    def start_prefetch(self) -> None:
        self._append("Initializing the configured Whisper model.\n")
        self._launch(lambda _report, _cancel: self._prefetch())

    @staticmethod
    def _prefetch() -> dict[str, object]:
        from src.stt_engine import STTEngine

        settings = VideoTranslationApplication().load_settings()
        STTEngine(settings)
        return {"status": "success", "whisper_model": settings.whisper_model}

    def open_runtime_folder(self) -> None:
        path = self.runtime["root"]
        try:
            import os
            import subprocess
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif __import__("sys").platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Cannot open folder", str(exc), parent=self.root)

    def cancel_processing(self) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            self.worker.cancel()
            self.cancel.configure(state="disabled")
            self.status.set("Cancellation requested…")
            self._append("Cancellation requested; the pipeline will stop at a safe stage boundary.\n")

    def _report(self, event: dict[str, object]) -> None:
        self.root.after(0, lambda: self._apply_event(event))

    def _apply_event(self, event: dict[str, object]) -> None:
        stage = str(event.get("stage", "processing"))
        message = str(event.get("message", ""))
        percent = event.get("percent")
        if isinstance(percent, (int, float)):
            self.progress["value"] = max(0, min(100, percent))
        if stage == "finished":
            self._busy(False)
            self.status.set("Completed")
            self._append(message + "\n")
        elif stage == "cancelled":
            self._busy(False)
            self.status.set("Cancelled")
            self._append(message + "\n")
        elif stage == "error":
            self._busy(False)
            self.status.set("Error")
            self._append(message + "\n")
            messagebox.showerror("Processing error", message, parent=self.root)
        else:
            completed = event.get("completed")
            total = event.get("total")
            suffix = f" ({completed}/{total})" if total else ""
            self.status.set(f"{stage.replace('_', ' ').title()}{suffix}")
            self._append(f"[{stage}] {message}\n")

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")


def main() -> int:
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
