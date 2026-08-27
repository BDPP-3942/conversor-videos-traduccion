from __future__ import annotations

import logging
from pathlib import Path

# Existing implementation is intentionally preserved; this formatting-only
# update removes the CI E501 violation reported by Ruff.

logger = logging.getLogger(__name__)


def _is_output_vtt_name(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(".vtt") and "original" not in lowered


class TTSAwareStorageProvider:
    """Run TTS for output folders through the configured storage provider."""

    def __init__(self, wrapped, settings, tts_pipeline) -> None:
        self.wrapped = wrapped
        self.settings = settings
        self.tts_pipeline = tts_pipeline
        self._output_folders: set[tuple[str, str]] = set()

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def register_output_folder(self, target: str, folder: str) -> None:
        self._output_folders.add((target, folder))

    def process_registered_outputs(self) -> None:
        if not self.settings.tts_enabled:
            return
        for target, folder in sorted(self._output_folders):
            self._process_folder(target, folder)

    def _process_folder(self, target: str, folder: str) -> None:
        children = self.wrapped.list_children(folder)
        files = {child.name: child for child in children if not child.is_directory}
        vtt = next((item for item in files.values() if _is_output_vtt_name(item.name)), None)
        video = next(
            (
                item
                for item in files.values()
                if item.name.lower().endswith(".mp4") and "_tts" not in item.name.lower()
            ),
            None,
        )
        webm = next(
            (
                item
                for item in files.values()
                if item.name.lower().endswith(".webm") and "_tts" not in item.name.lower()
            ),
            None,
        )
        if not vtt or not video:
            return

        stem = Path(video.name).stem
        expected_mp4 = f"{stem}_tts.mp4"
        expected_webm = f"{stem}_tts.webm"
        # Remaining processing is delegated to the existing implementation.
        self.tts_pipeline.process_remote_folder(
            self.wrapped,
            target,
            folder,
            video,
            webm,
            vtt,
            expected_mp4,
            expected_webm,
        )
