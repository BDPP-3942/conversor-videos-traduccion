from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("webvtt")

from config.settings import AppSettings
from src.storage.base import StorageFile, StorageProvider
from src.subtitle_repair import repair_output_subtitles
from src.vtt_builder import VTTBuilder


class FakeStorage(StorageProvider):
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, location: str) -> Path:
        path = Path(location)
        if not path.is_absolute():
            path = self.root / location
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_zip_files(self, location: str):
        return []

    def download_file(self, file: StorageFile, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(Path(file.id).read_bytes())

    def upload_file(self, local_path: Path, location: str, mime_type=None) -> StorageFile:
        target_dir = self._path(location)
        target = target_dir / local_path.name
        target.write_bytes(local_path.read_bytes())
        return StorageFile(id=str(target), name=target.name)

    def ensure_folder(self, parent: str, name: str) -> str:
        path = self._path(parent) / name
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def folder_exists(self, parent: str, name: str) -> bool:
        return (self._path(parent) / name).is_dir()

    def file_exists(self, parent: str, name: str) -> bool:
        return (self._path(parent) / name).is_file()

    def list_children(self, parent: str) -> list[StorageFile]:
        path = Path(parent) if Path(parent).is_absolute() else self._path(parent)
        if not path.is_dir():
            return []
        return [StorageFile(id=str(item), name=item.name, is_directory=item.is_dir()) for item in path.iterdir()]

    def delete_folder(self, parent: str, name: str) -> None:
        import shutil

        folder = self._path(parent) / name
        if folder.is_dir():
            shutil.rmtree(folder)


def _settings() -> AppSettings:
    return AppSettings(
        provider="local",
        target="local://storage/output",
        target_lang="en",
        source_lang="es",
        original_transcript_subdir="original_transcriptions",
        translation_retries=1,
        translation_batch_size=4,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )


def _fixture(tmp_path: Path, invalid_original: bool, invalid_translation: bool):
    folder = tmp_path / "37x02_Tema"
    original_dir = folder / "original_transcriptions"
    original_dir.mkdir(parents=True)
    (folder / "37x02_Tema.mp4").write_bytes(b"mp4")
    if invalid_original:
        (original_dir / "37x02_Tema_original.vtt").write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:00.000\nhola\n",
            encoding="utf-8",
        )
    else:
        VTTBuilder.generate_vtt(
            [{"start": 0, "end": 1, "text": "hola"}],
            original_dir / "37x02_Tema_original.vtt",
        )
    if invalid_translation:
        (folder / "37x02_Tema_en.vtt").write_text(
            "WEBVTT\n\n00:00:05.000 --> 00:00:02.000\nhello\n",
            encoding="utf-8",
        )
    else:
        VTTBuilder.generate_vtt(
            [{"start": 0, "end": 1, "text": "hello"}],
            folder / "37x02_Tema_en.vtt",
        )
    return FakeStorage(tmp_path), folder


class FakeSTT:
    def transcribe(self, media_path: Path):
        return [
            {"start": 0, "end": 1, "text": "hola"},
            {"start": 2, "end": 3, "text": "mundo"},
        ]


class FakeTranslator:
    def translate_segments(self, segments):
        return [{"start": item["start"], "end": item["end"], "text": f"EN:{item['text']}"} for item in segments]


def test_both_invalid_rebuilds_stt_and_translation(tmp_path: Path, monkeypatch):
    storage, folder = _fixture(tmp_path, True, True)
    monkeypatch.setattr("src.stt_engine.STTEngine", lambda settings: FakeSTT())
    monkeypatch.setattr("src.translator.TextTranslator", lambda settings: FakeTranslator())

    result = repair_output_subtitles(storage, _settings(), str(folder))

    assert result["status"] == "repaired"
    assert result["original_repaired"] is True
    assert result["translated_repaired"] is True
    assert result["stt_regenerated"] is True
    assert result["backups"]
    assert list((folder / "original_transcriptions").glob("*.bak*"))
    assert list(folder.glob("*.bak*"))


def test_translation_invalid_reuses_original_timestamps(tmp_path: Path, monkeypatch):
    storage, folder = _fixture(tmp_path, False, True)
    monkeypatch.setattr("src.translator.TextTranslator", lambda settings: FakeTranslator())
    monkeypatch.setattr(
        "src.stt_engine.STTEngine",
        lambda settings: (_ for _ in ()).throw(AssertionError("STT must not run")),
    )

    result = repair_output_subtitles(storage, _settings(), str(folder))

    assert result["original_repaired"] is False
    assert result["translated_repaired"] is True
    assert result["stt_regenerated"] is False
    assert result["backups"]


def test_valid_subtitles_are_not_regenerated(tmp_path: Path, monkeypatch):
    storage, folder = _fixture(tmp_path, False, False)
    monkeypatch.setattr(
        "src.stt_engine.STTEngine",
        lambda settings: (_ for _ in ()).throw(AssertionError("STT must not run")),
    )
    monkeypatch.setattr(
        "src.translator.TextTranslator",
        lambda settings: (_ for _ in ()).throw(AssertionError("translation must not run")),
    )

    result = repair_output_subtitles(storage, _settings(), str(folder))

    assert result["status"] == "valid"
    assert result["original_repaired"] is False
    assert result["translated_repaired"] is False
