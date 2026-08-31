from __future__ import annotations

from types import SimpleNamespace

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
        self.children = {"folder": [StorageFile("file", "video.mp4", False)]}

    def list_children(self, parent: str):
        return self.children.get(parent, [])

    def delete_folder(self, parent: str, name: str) -> None:
        del parent
        for child in self.list_children(name):
            self._service.files().update(fileId=child.id, body={"trashed": True}, fields="id").execute()
        self._service.files().update(fileId=name, body={"trashed": True}, fields="id").execute()


class FakeRcloneStorage(RcloneStorageProvider):
    def __init__(self):
        self.remote = "remote"
        self.commands: list[list[str]] = []

    def _run(self, args):
        self.commands.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def delete_folder(self, parent: str, name: str) -> None:
        del parent
        self._run(["purge", f"{self.remote}:{name}"])


def test_google_drive_public_delete_contract_trashes_tree():
    storage = FakeDriveStorage()
    storage.delete_folder("root", "folder")
    assert storage._service.trashed == ["file", "folder"]


def test_rclone_public_delete_contract_uses_purge():
    storage = FakeRcloneStorage()
    storage.delete_folder("root", "backup")
    assert storage.commands == [["purge", "remote:backup"]]
