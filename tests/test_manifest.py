import json
from pathlib import Path

import pytest

from src.manifest import MANIFEST_VERSION, read_manifest, write_manifest


def test_manifest_round_trip_preserves_unicode(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    entries = [{"source": "Café/Lección_ñ.mp4", "output_folder": "Caféx01_Lección"}]

    write_manifest(path, entries, metadata={"title": "Vídeo"})

    assert read_manifest(path) == {
        "version": MANIFEST_VERSION,
        "metadata": {"title": "Vídeo"},
        "entries": entries,
    }
    assert "Café" in path.read_text(encoding="utf-8")
    assert not list(tmp_path.glob(".manifest.json.*.tmp"))


def test_manifest_publication_replaces_previous_complete_document(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    write_manifest(path, [{"source": "one"}])
    write_manifest(path, [{"source": "two"}])

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["entries"] == [{"source": "two"}]
    assert not list(tmp_path.glob(".manifest.json.*.tmp"))


def test_manifest_corruption_is_not_treated_as_empty_state(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="unreadable or corrupt"):
        read_manifest(path)
