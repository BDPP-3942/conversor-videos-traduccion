from __future__ import annotations

from pathlib import Path

import pytest

from src.tts_assets import ensure_tts_assets


def test_tts_assets_keep_existing_files(tmp_path: Path, monkeypatch) -> None:
    model = tmp_path / "model.onnx"
    voices = tmp_path / "voices.bin"
    model.write_bytes(b"model")
    voices.write_bytes(b"voices")

    def fail(*_args, **_kwargs):
        raise AssertionError("no debe descargarse un recurso existente")

    monkeypatch.setattr("src.tts_assets.urllib.request.urlopen", fail)
    assert ensure_tts_assets(model, voices) == (model, voices)


def test_tts_asset_urls_are_restricted_to_github() -> None:
    from src import tts_assets

    with pytest.raises(ValueError):
        tts_assets._download("http://example.com/model", Path("model"))
