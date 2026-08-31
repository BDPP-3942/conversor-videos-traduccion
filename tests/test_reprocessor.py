from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("webvtt")

from config.settings import AppSettings
from src.reprocessor import SubtitleReprocessor
from src.storage.base import StorageFile, StorageProvider
from src.vtt_builder import VTTBuilder


class FakeStorage(StorageProvider):
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, location: str) -> Path:
        raw = Path(location)
        path = raw if raw.is_absolute() else self.root / location.strip("/")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_zip_files(self, location: str):
        return []

    def download_file(self, file: StorageFile, destination: Path) -> None:
        source = Path(file.id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())

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
        return [
            StorageFile(id=str(item), name=item.name, is_directory=item.is_dir())
            for item in sorted(path.iterdir(), key=lambda item: item.name)
        ]


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


class FakeSTT:
    calls = 0

    def transcribe(self, media_path: Path):
        type(self).calls += 1
        return [
            {"start": 0, "end": 1.0, "text": "hola"},
            {"start": 3.0, "end": 4.0, "text": "mundo"},
        ]


class FakeTranslator:
    calls = 0

    def translate_segments(self, segments):
        type(self).calls += 1
        return [{"start": item["start"], "end": item["end"], "text": f"EN:{item['text']}"} for item in segments]


def _fixture(tmp_path: Path):
    storage = FakeStorage(tmp_path)
    folder = tmp_path / "37x02_Tema"
    original_dir = folder / "original_transcriptions"
    original_dir.mkdir(parents=True)
    (folder / "37x02_Tema.mp4").write_bytes(b"mp4")
    (folder / "37x02_Tema.webm").write_bytes(b"webm")
    (folder / "37x02_Tema_en.vtt").write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nOLD\n", encoding="utf-8"
    )
    VTTBuilder.generate_vtt(
        [
            {"start": 0, "end": 1, "text": "antiguo"},
            {"start": 3, "end": 4, "text": "texto"},
        ],
        original_dir / "37x02_Tema_original.vtt",
    )
    return storage, folder


def test_stt_only_reuses_existing_video_and_preserves_folder(tmp_path: Path):
    storage, folder = _fixture(tmp_path)
    FakeSTT.calls = 0
    result = SubtitleReprocessor(_settings(), storage).reprocess(
        str(tmp_path),
        mode="stt_only",
        output_folder=folder.name,
        stt_engine_factory=FakeSTT,
    )
