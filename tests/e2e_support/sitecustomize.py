from __future__ import annotations

import os
from pathlib import Path


class _FakeSTT:
    def __init__(self, settings):
        self.settings = settings

    def transcribe(self, media_path):
        del media_path
        return [
            {"start": 0.0, "end": 0.5, "text": "hola"},
            {"start": 0.6, "end": 1.0, "text": "mundo"},
        ]


class _FakeTranslator:
    def __init__(self, settings):
        self.settings = settings

    def translate_segments(self, segments):
        return [{"start": item["start"], "end": item["end"], "text": f"EN:{item['text']}"} for item in segments]


def _install():
    from config import settings as app_settings
    from src import stt_engine, translator

    storage_root = os.environ.get("E2E_STORAGE_DIR")
    if storage_root:
        app_settings.STORAGE_DIR = Path(storage_root).resolve()
    stt_engine.STTEngine = _FakeSTT
    translator.TextTranslator = _FakeTranslator


_install()
