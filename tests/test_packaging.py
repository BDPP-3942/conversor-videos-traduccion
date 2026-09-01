from __future__ import annotations

import zipfile
from pathlib import Path


def _wheel_path() -> Path:
    candidates = sorted(Path("dist").glob("*.whl"))
    assert candidates, "python -m build did not produce a wheel"
    return candidates[-1]


def test_wheel_contains_default_config_and_console_entry_points() -> None:
    wheel = _wheel_path()
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert "config/app.toml" in names
        context_resources = {name for name in names if name.startswith("config/palabras_contexto.")}
        assert context_resources, "wheel does not contain config/palabras_contexto.*"
        entry_points = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        assert entry_points, "wheel has no console entry-point metadata"
        metadata = archive.read(entry_points[0]).decode("utf-8")

    expected = {
        "video-translation-pipeline = main:main",
        "video-translation-regenerate = src.regeneration:main",
        "video-subtitle-qa = src.subtitle_qa_cli:main",
        "video-translation-tts = src.tts_cli:main",
    }
    assert expected.issubset(set(metadata.splitlines()))
