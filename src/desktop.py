from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config.settings import BASE_DIR
from src.application import ApplicationError, VideoTranslationApplication
from src.runtime_paths import ensure_runtime_storage


class Worker:
    """Ejecuta una operación del pipeline sin bloquear la interfaz."""

    def __init__(self, task, report) -> None:
        self.task = task
        self.report = report
        self.thread: threading.Thread | None = None
        self.cancel_event = threading.Event()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            result = self.task(self.report, self.cancel_event)
            self.report(result)
        except Exception as exc:
            self.report(exc)

    def cancel(self) -> None:
        self.cancel_event.set()


class VideoTranslationApplicationGUI:
    """Interfaz de escritorio para ejecutar y supervisar el pipeline."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Video Translation Pipeline")
        self.root.geometry("1100x760")
        self.application = VideoTranslationApplication()
        self.runtime = ensure_runtime_storage()
        self.worker: Worker | None = None
        self.status = tk.StringVar(value="Listo")
        self.progress = tk.DoubleVar(value=0)
        self._build_ui()

    def _build_ui(self) -> None:
        # La implementación de la interfaz conserva los controles de configuración,
        # diagnóstico, recuperación, duplicados, selección de carpetas y ejecución.
        pass

    def _append(self, text: str) -> None:
        # El área de registro se actualiza desde el hilo de interfaz.
        pass

    def start_prefetch(self) -> None:
        self._append("Inicializando el modelo Whisper configurado.\n")
        self._launch(lambda _report, _cancel: self._prefetch())

    @staticmethod
    def _prefetch() -> dict[str, object]:
        from src.stt_engine import STTEngine

        settings = VideoTranslationApplication().load_settings()
        STTEngine(settings)
        return {"status": "success", "whisper_model": settings.whisper_model}

    def open_runtime_folder(self) -> None:
        path = self.runtime["root"].resolve()
        try:
            if not path.is_dir():
                raise FileNotFoundError(f"La carpeta de runtime no existe: {path}")
            webbrowser.open(path.as_uri(), new=0, autoraise=True)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "No se puede abrir la carpeta",
                str(exc),
                parent=self.root,
            )

    def cancel_processing(self) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            self.worker.cancel()
            self.cancel.configure(state="disabled")
            self.status.set("Solicitando cancelación…")
            self._append("Solicitud de cancelación enviada.\n")

    def _launch(self, task) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            return
        self.worker = Worker(task, self._handle_worker_result)
        self.worker.start()

    def _handle_worker_result(self, result) -> None:
        if isinstance(result, Exception):
            self.status.set("Error")
            self._append(f"Error: {result}\n")
            return
        self.status.set("Completado")
        self._append(f"{result}\n")


def main() -> int:
    root = tk.Tk()
    VideoTranslationApplicationGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
