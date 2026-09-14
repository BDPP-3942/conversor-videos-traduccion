from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.application import ApplicationError, VideoTranslationApplication


class Worker:
    def __init__(self, options: dict[str, object], report) -> None:
        self.options = options
        self.report = report
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, name="pipeline-worker", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            result = VideoTranslationApplication().run(progress=self.report, **self.options)
            self.report({"stage": "finished", "message": str(result), "result": result})
        except ApplicationError as exc:
            self.report({"stage": "error", "message": str(exc)})
        except Exception as exc:
            self.report({"stage": "error", "message": f"Unexpected error: {type(exc).__name__}: {exc}"})


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Video Translation Pipeline")
        self.root.geometry("980x720")
        self.root.minsize(760, 560)
        self.worker: Worker | None = None
        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self.root, padding=16)
        root.pack(fill="both", expand=True)

        paths = ttk.LabelFrame(root, text="Input and output", padding=12)
        paths.pack(fill="x", pady=(0, 12))
        self.source = tk.StringVar(value=str(Path("storage/input").resolve()))
        self.target = tk.StringVar(value=str(Path("storage/output").resolve()))
        self._path_row(paths, 0, "Input folder", self.source)
        self._path_row(paths, 1, "Output folder", self.target)

        processing = ttk.LabelFrame(root, text="Processing", padding=12)
        processing.pack(fill="x", pady=(0, 12))
        self.provider = tk.StringVar(value="local")
        self.translation = tk.StringVar(value="mistral")
        self.source_lang = tk.StringVar(value="es")
        self.target_lang = tk.StringVar(value="en")
        self.parallel = tk.IntVar(value=0)
        self.webm = tk.BooleanVar(value=False)
        self.tts = tk.BooleanVar(value=False)
        self._combo_row(processing, 0, "Storage provider", self.provider, ["local", "google_drive", "rclone"])
        self._combo_row(processing, 1, "Translation provider", self.translation, ["mistral", "local", "deepl", "mymemory"])
        self._entry_row(processing, 2, "Source language", self.source_lang)
        self._entry_row(processing, 3, "Target language", self.target_lang)
        ttk.Label(processing, text="Parallel videos (0 = AUTO)").grid(
            row=4, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Spinbox(processing, from_=0, to=64, textvariable=self.parallel, width=8).grid(
            row=4, column=1, sticky="w", pady=4
        )
        ttk.Checkbutton(processing, text="Generate secondary WebM", variable=self.webm).grid(
            row=5, column=1, sticky="w", pady=4
        )
        ttk.Checkbutton(processing, text="Enable synchronized TTS", variable=self.tts).grid(
            row=6, column=1, sticky="w", pady=4
        )
        processing.columnconfigure(1, weight=1)

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(0, 8))
        self.start = ttk.Button(actions, text="Start processing", command=self.start_processing)
        self.start.pack(side="left")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=16)

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 8))
        self.log = tk.Text(root, height=14, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _path_row(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Browse…", command=lambda: self._browse(variable)).grid(
            row=row, column=2, padx=(8, 0)
        )
        parent.columnconfigure(1, weight=1)

    @staticmethod
    def _entry_row(parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

    @staticmethod
    def _combo_row(parent, row: int, label: str, variable: tk.StringVar, values: list[str]) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            parent, textvariable=variable, values=values, state="readonly", width=20
        ).grid(row=row, column=1, sticky="w", pady=4)

    @staticmethod
    def _browse(variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=variable.get())
        if selected:
            variable.set(selected)

    def start_processing(self) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            return
        options = {
            "source": self.source.get(),
            "target": self.target.get(),
            "provider": self.provider.get(),
            "source_lang": self.source_lang.get().strip(),
            "target_lang": self.target_lang.get().strip(),
            "translation_provider": self.translation.get(),
            "max_parallel_videos": self.parallel.get(),
            "generate_webm": self.webm.get(),
            "tts_enabled": self.tts.get(),
        }
        self.start.configure(state="disabled")
        self.status.set("Processing…")
        self.progress.start(12)
        self._append("Starting processing in a background worker.\n")
        self.worker = Worker(options, self._report)
        self.worker.start()

    def _report(self, event: dict[str, object]) -> None:
        self.root.after(0, lambda: self._apply_event(event))

    def _apply_event(self, event: dict[str, object]) -> None:
        stage = str(event.get("stage", "processing"))
        message = str(event.get("message", ""))
        if stage == "finished":
            self.progress.stop()
            self.start.configure(state="normal")
            self.status.set("Completed")
            self._append(message + "\n")
        elif stage == "error":
            self.progress.stop()
            self.start.configure(state="normal")
            self.status.set("Error")
            self._append(message + "\n")
            messagebox.showerror("Processing error", message, parent=self.root)
        else:
            self.status.set(message or stage.title())
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
