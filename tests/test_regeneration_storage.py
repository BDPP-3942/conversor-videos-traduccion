from __future__ import annotations

from types import SimpleNamespace

import src.regeneration as regeneration
from src.storage.base import StorageFile
from src.storage.google_drive import GoogleDriveStorageProvider
from src.storage.rclone import RcloneStorageProvider


class FakeDriveService:
    def __init__(self):
        self.trashed: list[str] = []

    def files(self):
        return self

    def update(self, *, fileId, body, fields):
        assert fields == "id"
        if body == {"trashed": True}:
            self.trashed.append(fileId)
        return self

    def execute(self):
        return {"id": self.trashed[-1]}


class FakeDriveStorage(GoogleDriveStorageProvider):
    def __init__(self):
        self._service = FakeDriveService()
        self.children = {
            "root": [StorageFile("folder", "backup", True)],
            "folder": [StorageFile("file", "video.mp4", False)],
        }

    def list_children(self, parent: str):
        return self.children.get(parent, [])


class FakeRcloneStorage(RcloneStorageProvider):
    def __init__(self):
        self.remote = "remote"
        self.commands: list[list[str]] = []

    def _run(self, args):
        self.commands.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_google_drive_cleanup_recursively_trashes_tree():
    storage = FakeDriveStorage()

    regeneration._delete_folder(storage, "folder")

    assert storage._service.trashed == ["file", "folder"]


def test_rclone_cleanup_uses_purge_for_backup_tree():
    storage = FakeRcloneStorage()

    regeneration._delete_folder(storage, "backup")

    assert storage.commands == [["purge", "remote:backup"]]
