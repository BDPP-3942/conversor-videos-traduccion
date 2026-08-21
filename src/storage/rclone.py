from __future__ import annotations

import json
import mimetypes
import subprocess
from pathlib import Path

from src.file_naming import normalize_component, normalize_filename
from src.storage.base import StorageFile, StorageProvider


class RcloneStorageProvider(StorageProvider):
    """Adaptador opcional de compatibilidad."""

    def __init__(self, binary_file: Path, config_file: Path, remote: str) -> None:
        self.binary_file = binary_file
        self.config_file = config_file
        self.remote = remote
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.binary_file.is_file():
            raise FileNotFoundError(
                f"Managed rclone executable not found: {self.binary_file}. "
                "Run `python main.py provider bootstrap` or enable the rclone provider setup."
            )
        if not self.config_file.is_file():
            raise FileNotFoundError(
                f"rclone configuration not found: {self.config_file}. "
                "Run `python main.py provider auth-rclone ...` first."
            )

    def _run(self, args: list[str]) -> str:
        command = [str(self.binary_file), "--config", str(self.config_file), *args]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=300)
        except FileNotFoundError as exc:
            raise RuntimeError("rclone is not installed or not available in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("rclone command timed out") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "rclone failed").strip()) from exc
        return result.stdout

    def _items(self, location: str) -> list[dict]:
        raw = self._run(["lsjson", f"{self.remote}:{location}"])
        return json.loads(raw) if raw else []

    def list_zip_files(self, location: str) -> list[StorageFile]:
        items = self._items(location)
        return [
            StorageFile(id=f"{location.rstrip('/')}/{item['Name']}", name=item["Name"])
            for item in items
            if not item.get("IsDir") and item.get("Name", "").lower().endswith(".zip")
        ]

    def download_file(self, file: StorageFile, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._run(["copyto", f"{self.remote}:{file.id}", str(destination)])

    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        target = f"{self.remote}:{location.rstrip('/')}/{local_path.name}"
        args = ["copyto", str(local_path), target]
        detected = mime_type or mimetypes.guess_type(local_path.name)[0]
        if detected:
            args.extend(["--metadata-set", f"content-type={detected}"])
        self._run(args)
        return StorageFile(id=f"{location.rstrip('/')}/{local_path.name}", name=local_path.name)

    def folder_exists(self, parent: str, name: str) -> bool:
        location = f"{parent.rstrip('/')}/{name}"
        try:
            self._run(["lsjson", f"{self.remote}:{location}", "--dirs-only"])
            return True
        except RuntimeError:
            return False

    def file_exists(self, parent: str, name: str) -> bool:
        raw = self._run(["lsjson", f"{self.remote}:{parent.rstrip('/')}", "--files-only"])
        items = json.loads(raw) if raw else []
        return any(item.get("Name") == name for item in items)

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        renamed: dict[str, str] = {}
        for item in self._items(target):
            if not item.get("IsDir"):
                continue
            old = item["Name"]
            new = normalize_component(old)
            current_path = f"{target.rstrip('/')}/{old}"
            target_name = new
            if new != old and not self.folder_exists(target, new):
                self._run(["moveto", f"{self.remote}:{current_path}", f"{self.remote}:{target.rstrip('/')}/{new}"])
                renamed[old] = new
                old = new
            folder_path = f"{target.rstrip('/')}/{old}"
            for child in self._items(folder_path):
                if child.get("IsDir"):
                    continue
                normalized = normalize_filename(child["Name"])
                if normalized != child["Name"] and not self.file_exists(folder_path, normalized):
                    self._run([
                        "moveto",
                        f"{self.remote}:{folder_path}/{child['Name']}",
                        f"{self.remote}:{folder_path}/{normalized}",
                    ])
        return renamed

    def ensure_folder(self, parent: str, name: str) -> str:
        location = f"{parent.rstrip('/')}/{name}"
        if not self.folder_exists(parent, name):
            self._run(["mkdir", f"{self.remote}:{location}"])
        return location

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        if status != "success":
            return
        archive = f"{self.remote}:{self._archive_path()}"
        source = f"{self.remote}:{file.id}"
        self._run(["moveto", source, f"{archive.rstrip('/')}/{file.name}"])

    def _archive_path(self) -> str:
        return "archive"
