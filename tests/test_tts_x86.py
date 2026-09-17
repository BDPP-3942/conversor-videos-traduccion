from __future__ import annotations

import sys
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from src.tts_pipeline import WindowsSAPIProvider, create_tts_provider


def test_windows_x86_uses_sapi_provider(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("src.tts_pipeline.platform.system", lambda: "Windows")
    monkeypatch.setattr("struct.calcsize", lambda _: 4)
    provider = create_tts_provider(SimpleNamespace(tts_provider="kokoro"))
    assert isinstance(provider, WindowsSAPIProvider)


def test_sapi_provider_reads_generated_pcm(monkeypatch, tmp_path: Path) -> None:
    class FakeEngine:
        def getProperty(self, name):
            return [SimpleNamespace(id="voice", name="English")]

        def setProperty(self, _name, _value):
            return None

        def save_to_file(self, _text, filename):
            with wave.open(filename, "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(22050)
                handle.writeframes((np.zeros(2205, dtype=np.int16)).tobytes())

        def runAndWait(self):
            return None

        def stop(self):
            return None

    monkeypatch.setitem(sys.modules, "pyttsx3", SimpleNamespace(init=lambda driverName=None: FakeEngine()))
    samples, sample_rate = WindowsSAPIProvider().synthesize(
        "hola",
        language="es",
        voice="voice",
        speed=1.0,
    )
    assert sample_rate == 22050
    assert len(samples) == 2205
