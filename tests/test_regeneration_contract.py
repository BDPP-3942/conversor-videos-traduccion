from __future__ import annotations

from pathlib import Path

import pytest

from src.storage.local import LocalStorageProvider


class FakeGoogleDriveStorage(LocalStorageProvider):
    """Filesystem-backed stand-in for the Google Drive adapter."""


class FakeRcloneStorage(LocalStorageProvider):
    """Filesystem-backed stand-in for the rclone adapter."""


@pytest.mark.parametrize("provider_type", [FakeGoogleDriveStorage, FakeRcloneStorage])
def test_remote_provider_fakes_support_backup_rollback_and_commit(tmp_path: Path, provider_type):
    provider = provider_type()
    target = tmp_path / "output"
    target.mkdir()
    original = target / "lesson"
    original.mkdir()
    (original / "video.mp4").write_bytes(b"old")

    backed_up = provider.backup_output_folder(
        str(target), "lesson", ".regeneration-backup-run-lesson", "original_transcriptions"
    )
    assert backed_up is True
    assert not original.exists()
    assert (target / ".regeneration-backup-run-lesson").is_dir()

    restored = provider.restore_output_backup(
        str(target), ".regeneration-backup-run-lesson", "lesson", "original_transcriptions"
    )
    assert restored is True
    assert (original / "video.mp4").read_bytes() == b"old"

    provider.backup_output_folder(str(target), "lesson", ".regeneration-backup-run-lesson", "original_transcriptions")
    target.joinpath("lesson").mkdir()
    (target / "lesson" / "video.mp4").write_bytes(b"new")
    provider.delete_output_backup(str(target), ".regeneration-backup-run-lesson")
    assert not (target / ".regeneration-backup-run-lesson").exists()
    assert (target / "lesson" / "video.mp4").read_bytes() == b"new"
