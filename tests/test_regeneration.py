from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import src.regeneration as regeneration
from src.storage.base import StorageFile
from src.storage.local import LocalStorageProvider


class FakeStorage(LocalStorageProvider):
    def __init__(self, root: Path) -> None:
        super().__init__()
        self.source = root / "input"
        self.target = root / "output"
        self.source.mkdir(parents=True)
        self.target.mkdir(parents=True)
        (self.source / "video.zip").write_bytes(b"source")

    def list_zip_files(self, location: str) -> list[StorageFile]:
        del location
        return [StorageFile(id=str(self.source / "video.zip"), name="video.zip")]

    def folder_exists(self, parent: str, name: str) -> bool:
        del parent
        return (self.target / name).is_dir()

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        del target, original_transcript_subdir
        old = self.target / old_name
        new = self.target / new_name
        old.rename(new)
        return {old_name: new_name}

    def delete_folder(self, parent: str, name: str) -> None:
        del parent
        folder = self.target / name
        if folder.exists():
            import shutil

            shutil.rmtree(folder)

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class FakeSettings:
    provider: str = "local"
    original_transcript_subdir: str = "original_transcriptions"
    source: str = "local://input"
    target: str = "local://output"


class FakePipeline:
    def __init__(self, settings, storage):
        del settings
        self.storage = storage

    def run(self, source: str, target: str, *, force_reprocess: bool = False, finalize_source: bool = True):
        assert force_reprocess is True
        assert finalize_source is False
        del source, target
        output = self.storage.target / "lesson"
        output.mkdir()
        (output / "video.mp4").write_bytes(b"new")
        return {"status": "success", "videos": [{"output_folder": "lesson"}]}


def _settings():
    return FakeSettings()


def _patch(monkeypatch, tmp_path, manifest_dir, storage):
    monkeypatch.setattr(regeneration, "create_storage_provider", lambda provider, settings: storage)
    monkeypatch.setattr(
        regeneration,
        "resolve_project_path",
        lambda value: Path(value) if Path(value).is_absolute() else tmp_path / value,
    )
    monkeypatch.setattr(
        regeneration,
        "_manifest_local_path",
        lambda name: manifest_dir / f"{Path(name).stem}.json",
    )
    monkeypatch.setattr("src.pipeline.MediaPipeline", FakePipeline)


def test_regeneration_success_uses_common_pipeline_and_cleans_backup(monkeypatch, tmp_path):
    storage = FakeStorage(tmp_path)
    old = storage.target / "lesson"
    old.mkdir()
    (old / "video.mp4").write_bytes(b"old")
    (old / "old_artifact.xyz").write_bytes(b"obsolete")
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "video.json").write_text(
        '{"entries":[{"source":"lesson.mp4","status":"success","output_folder":"lesson"}]}',
        encoding="utf-8",
    )
    _patch(monkeypatch, tmp_path, manifest_dir, storage)

    result = regeneration.regenerate("input", "output", _settings())

    assert result["status"] == "success"
    assert result["source_preserved"] is True
    assert (storage.source / "video.zip").is_file()
    assert (storage.target / "lesson" / "video.mp4").read_bytes() == b"new"
    assert not (storage.target / "lesson" / "old_artifact.xyz").exists()
    assert not any(storage.target.glob(".regeneration-backup-*"))


def test_regeneration_failure_restores_previous_output(monkeypatch, tmp_path):
    storage = FakeStorage(tmp_path)
    old = storage.target / "lesson"
    old.mkdir()
    (old / "video.mp4").write_bytes(b"old")
    (old / "old_artifact.xyz").write_bytes(b"obsolete")
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "video.json").write_text(
        '{"entries":[{"source":"lesson.mp4","status":"success","output_folder":"lesson"}]}',
        encoding="utf-8",
    )

    class FailingPipeline(FakePipeline):
        def run(self, source, target, *, force_reprocess=False, finalize_source=True):
            assert force_reprocess is True
            assert finalize_source is False
            return {"status": "error"}

    monkeypatch.setattr(regeneration, "create_storage_provider", lambda provider, settings: storage)
    monkeypatch.setattr(
        regeneration,
        "_manifest_local_path",
        lambda name: manifest_dir / f"{Path(name).stem}.json",
    )
    monkeypatch.setattr("src.pipeline.MediaPipeline", FailingPipeline)

    try:
        regeneration.regenerate("input", "output", _settings())
    except regeneration.RegenerationError:
        pass
    else:
        raise AssertionError("Expected RegenerationError")

    assert (storage.target / "lesson" / "video.mp4").read_bytes() == b"old"
    assert (storage.target / "lesson" / "old_artifact.xyz").is_file()
    assert (storage.source / "video.zip").is_file()
