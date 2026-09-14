from __future__ import annotations

import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.application import ApplicationError, VideoTranslationApplication


class Worker(QObject):
    progress = Signal(dict)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, options: dict[str, object]) -> None:
        super().__init__()
        self.options = options
        self.cancel_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result = VideoTranslationApplication().run(
                progress=self.progress.emit,
                cancel_event=self.cancel_event,
                **self.options,
            )
            self.finished.emit(result)
        except ApplicationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Unexpected error: {type(exc).__name__}: {exc}")

    def cancel(self) -> None:
        self.cancel_event.set()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Video Translation Pipeline")
        self.resize(980, 720)
        self.thread: QThread | None = None
        self.worker: Worker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        paths = QGroupBox("Input and output")
        form = QFormLayout(paths)
        self.source = QLineEdit(str(Path("storage/input").resolve()))
        self.target = QLineEdit(str(Path("storage/output").resolve()))
        form.addRow("Input folder", self._path_row(self.source))
        form.addRow("Output folder", self._path_row(self.target))
        layout.addWidget(paths)

        processing = QGroupBox("Processing")
        form = QFormLayout(processing)
        self.provider = QComboBox(); self.provider.addItems(["local", "google_drive", "rclone"])
        self.translation = QComboBox(); self.translation.addItems(["mistral", "local", "deepl", "mymemory"])
        self.source_lang = QLineEdit("es"); self.target_lang = QLineEdit("en")
        self.parallel = QSpinBox(); self.parallel.setRange(0, 64); self.parallel.setSpecialValueText("AUTO")
        self.webm = QCheckBox("Generate secondary WebM")
        self.tts = QCheckBox("Enable synchronized TTS")
        form.addRow("Storage provider", self.provider)
        form.addRow("Translation provider", self.translation)
        form.addRow("Source language", self.source_lang)
        form.addRow("Target language", self.target_lang)
        form.addRow("Parallel videos", self.parallel)
        form.addRow("Outputs", self.webm)
        form.addRow("Voice synthesis", self.tts)
        layout.addWidget(processing)

        actions = QHBoxLayout()
        self.start = QPushButton("Start processing")
        self.start.setDefault(True)
        self.start.clicked.connect(self._start)
        self.cancel = QPushButton("Cancel")
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(self._cancel)
        actions.addWidget(self.start); actions.addWidget(self.cancel); actions.addStretch()
        layout.addLayout(actions)

        self.stage = QLabel("Ready")
        self.progress = QProgressBar(); self.progress.setRange(0, 100)
        layout.addWidget(self.stage); layout.addWidget(self.progress)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)
        self.setCentralWidget(root)

    @staticmethod
    def _path_row(field: QLineEdit) -> QWidget:
        row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0)
        browse = QPushButton("Browse…")
        browse.clicked.connect(lambda: MainWindow._browse(field))
        layout.addWidget(field, 1); layout.addWidget(browse)
        return row

    @staticmethod
    def _browse(field: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(None, "Select folder", field.text())
        if path:
            field.setText(path)

    def _start(self) -> None:
        options = {
            "source": self.source.text(),
            "target": self.target.text(),
            "provider": self.provider.currentText(),
            "source_lang": self.source_lang.text().strip(),
            "target_lang": self.target_lang.text().strip(),
            "translation_provider": self.translation.currentText(),
            "max_parallel_videos": self.parallel.value(),
            "generate_webm": self.webm.isChecked(),
            "tts_enabled": self.tts.isChecked(),
        }
        self._set_running(True)
        self.log.appendPlainText("Starting processing…")
        self.thread = QThread(self)
        self.worker = Worker(options)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self._thread_finished)
        self.thread.start()

    def _cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.stage.setText("Cancelling…")
            self.log.appendPlainText("Cancellation requested; current operation will finish cooperatively.")
            self.cancel.setEnabled(False)

    @Slot(dict)
    def _on_progress(self, event: dict) -> None:
        self.stage.setText(str(event.get("message", event.get("stage", "Processing"))))
        percent = event.get("percent")
        if isinstance(percent, int):
            self.progress.setValue(max(0, min(100, percent)))
        self.log.appendPlainText(f"[{event.get('stage', 'processing')}] {event.get('message', '')}")

    @Slot(dict)
    def _on_finished(self, result: dict) -> None:
        self.progress.setValue(100 if result.get("status") != "cancelled" else self.progress.value())
        self.stage.setText(f"Finished: {result.get('status', 'unknown')}")
        self.log.appendPlainText(str(result))

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.stage.setText("Error")
        self.log.appendPlainText(message)
        QMessageBox.critical(self, "Processing error", message)

    def _thread_finished(self) -> None:
        self._set_running(False)
        self.worker = None
        self.thread = None

    def _set_running(self, running: bool) -> None:
        self.start.setEnabled(not running)
        self.cancel.setEnabled(running)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Video Translation Pipeline")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
