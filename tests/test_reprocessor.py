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
    (folder / "37x02_Tema_en.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nOLD\n", encoding="utf-8")
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

    assert result["status"] == "success"
    assert result["ffmpeg_regenerated"] is False
    assert FakeSTT.calls == 1
    assert folder.is_dir()
    assert not (tmp_path / "37x02_Tema_01").exists()
    assert any(folder.joinpath("original_transcriptions").glob("*.bak.*"))


def test_translate_only_does_not_run_stt(tmp_path: Path):
    storage, folder = _fixture(tmp_path)
    FakeSTT.calls = 0
    FakeTranslator.calls = 0
    result = SubtitleReprocessor(_settings(), storage).reprocess(
        str(tmp_path),
        mode="translate_only",
        output_folder=folder.name,
        stt_engine_factory=lambda: (_ for _ in ()).throw(AssertionError("STT must not run")),
        translator_factory=FakeTranslator,
    )

    assert result["status"] == "success"
    assert FakeTranslator.calls == 1
    assert FakeSTT.calls == 0
    assert any(folder.glob("37x02_Tema_en.vtt.bak.*"))


def test_full_reprocess_updates_both_artifacts_and_marks_partial_translation(tmp_path: Path):
    storage, folder = _fixture(tmp_path)

    class PartialTranslator:
        def translate_segments(self, segments):
            return [
                {"start": 0, "end": 1, "text": "EN:hola", "translation_failed": True},
                {"start": 3, "end": 4, "text": "EN:mundo"},
            ]

    result = SubtitleReprocessor(_settings(), storage).reprocess(
        str(tmp_path),
        mode="full",
        output_folder=folder.name,
        stt_engine_factory=FakeSTT,
        translator_factory=PartialTranslator,
    )

    assert result["status"] == "partial_translation"
    assert result["translation_failed_segments"] == 1
    assert result["backup_transcription"]
    assert result["backup_translated_vtt"]
    assert (folder / "reprocess_history").is_dir()


def test_invalid_timestamps_do_not_replace_previous_vtt(tmp_path: Path):
    storage, folder = _fixture(tmp_path)
    original = folder / "original_transcriptions" / "37x02_Tema_original.vtt"
    before = original.read_bytes()

    class BadSTT:
        def transcribe(self, media_path: Path):
            return [{"start": 5, "end": 2, "text": "bad"}]

    try:
        SubtitleReprocessor(_settings(), storage).reprocess(
            str(tmp_path), mode="stt_only", output_folder=folder.name, stt_engine_factory=BadSTT
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid STT timestamps should fail validation")

    assert original.read_bytes() == before
    assert not any(folder.joinpath("original_transcriptions").glob("37x02_Tema_original.vtt.bak.*"))


def test_duplicate_structural_inventory_example_is_self_contained():
    inventory = """
    wetransfer_curso37_7o-opt-taich-bombeos-mp4_2026-07-20_1135.zip
        20 peng.mp4
        7º opt taich BOMBEOS.mp4
    wetransfer_7o-opt-taich-bombeos-mp4_2026-07-20_1135.zip
        20 peng.mp4
        7º opt taich BOMBEOS.mp4
    """
    assert inventory.count("wetransfer_curso37_7o-opt-taich-bombeos") == 1
    assert inventory.count("wetransfer_7o-opt-taich-bombeos") == 1
    assert inventory.count("20 peng.mp4") == 2


def test_repeated_reprocess_preserves_multiple_backups(tmp_path: Path):
    storage, folder = _fixture(tmp_path)
    reprocessor = SubtitleReprocessor(_settings(), storage)
    reprocessor.reprocess(str(tmp_path), mode="stt_only", output_folder=folder.name, stt_engine_factory=FakeSTT)
    reprocessor.reprocess(str(tmp_path), mode="stt_only", output_folder=folder.name, stt_engine_factory=FakeSTT)

    backups = list(folder.joinpath("original_transcriptions").glob("37x02_Tema_original.vtt.bak.*"))
    assert len(backups) == 2
    assert len({item.name for item in backups}) == 2


def test_invalid_translation_does_not_replace_existing_vtt(tmp_path: Path):
    storage, folder = _fixture(tmp_path)
    translated = folder / "37x02_Tema_en.vtt"
    before = translated.read_bytes()

    class BadTranslator:
        def translate_segments(self, segments):
            return [{"start": 5, "end": 2, "text": "invalid"}]

    try:
        SubtitleReprocessor(_settings(), storage).reprocess(
            str(tmp_path),
            mode="translate_only",
            output_folder=folder.name,
            translator_factory=BadTranslator,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid translation timestamps should fail validation")

    assert translated.read_bytes() == before
    assert not any(folder.glob("37x02_Tema_en.vtt.bak.*"))


def test_reprocess_all_stt_only_processes_every_eligible_existing_output(tmp_path: Path):
    storage, folder_one = _fixture(tmp_path)
    folder_two = tmp_path / "18x03_Otra"
    original_dir = folder_two / "original_transcriptions"
    original_dir.mkdir(parents=True)
    (folder_two / "18x03_Otra.mp4").write_bytes(b"mp4")
    VTTBuilder.generate_vtt(
        [{"start": 0, "end": 1, "text": "antiguo"}],
        original_dir / "18x03_Otra_original.vtt",
    )

    FakeSTT.calls = 0
    result = SubtitleReprocessor(_settings(), storage).reprocess_all(
        str(tmp_path), mode="stt_only", stt_engine_factory=FakeSTT
    )

    assert result["scope"] == "all"
    assert result["status"] == "success"
    assert result["total_candidates"] == 2
    assert result["processed"] == 2
    assert result["failed"] == 0
    assert FakeSTT.calls == 2
    assert folder_one.is_dir()
    assert folder_two.is_dir()
    assert not (tmp_path / "37x02_Tema_01").exists()


def test_reprocess_all_continues_after_one_folder_failure(tmp_path: Path):
    storage, _ = _fixture(tmp_path)
    good = tmp_path / "18x03_Otra"
    original_dir = good / "original_transcriptions"
    original_dir.mkdir(parents=True)
    (good / "18x03_Otra.mp4").write_bytes(b"mp4")
    VTTBuilder.generate_vtt(
        [{"start": 0, "end": 1, "text": "antiguo"}],
        original_dir / "18x03_Otra_original.vtt",
    )

    class SelectivelyBadSTT:
        calls = 0

        def transcribe(self, media_path: Path):
            type(self).calls += 1
            if type(self).calls == 1:
                return [{"start": 0, "end": 1, "text": "ok"}]
            return [{"start": 4, "end": 2, "text": "bad"}]

    result = SubtitleReprocessor(_settings(), storage).reprocess_all(
        str(tmp_path), mode="stt_only", stt_engine_factory=SelectivelyBadSTT
    )

    assert result["scope"] == "all"
    assert result["status"] in {"partial_failure", "error"}
    assert result["failed"] >= 1
    assert result["processed"] >= 1
    assert len(result["results"]) == 2


def test_reprocess_all_does_not_create_transcript_subdirs_in_unrelated_outputs(tmp_path: Path):
    storage = FakeStorage(tmp_path)
    unrelated = tmp_path / "not-a-video-output"
    unrelated.mkdir()
    (unrelated / "notes.txt").write_text("ignore", encoding="utf-8")

    result = SubtitleReprocessor(_settings(), storage).reprocess_all(str(tmp_path), mode="translate_only")

    assert result["total_candidates"] == 0
    assert not (unrelated / "original_transcriptions").exists()
