from __future__ import annotations

import json
import mimetypes
import subprocess
from pathlib import Path

from config import settings
from src.storage.base import StorageFile, StorageProvider


class RcloneStorageProvider(StorageProvider):
    """Adaptador opcional de compatibilidad. No forma parte del núcleo."""

    def __init__(self, config_file: Path, remote: str) -> None:
        if not config_file.is_file():
            raise FileNotFoundError(f"rclone config not found: {config_file}")
        self.config_file = config_file
        self.remote = remote

    def _run(self, args: list[str]) -> str:
        command = ["rclone", "--config", str(self.config_file), *args]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError("rclone is not installed or not available in PATH") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "rclone failed").strip()) from exc
        return result.stdout

    def list_zip_files(self, location: str) -> list[StorageFile]:
        target = f"{self.remote}:{location}"
        raw = self._run(["lsjson", target, "--include", "*.zip"])
        items = json.loads(raw) if raw else []
        return [
            StorageFile(id=item["Path"], name=item["Name"])
            for item in items
            if not item.get("IsDir") and item.get("Name", "").lower().endswith(".zip")
        ]

    def download_file(self, file: StorageFile, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                "copyto",
                f"{self.remote}:{file.id}",
                str(destination),
            ]
        )

    def upload_file(
        self,
        local_path: Path,
        location: str,
        mime_type: str | None = None,
    ) -> StorageFile:
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        target = f"{self.remote}:{location.rstrip('/')}/{local_path.name}"
        args = ["copyto", str(local_path), target]
        detected = mime_type or mimetypes.guess_type(local_path.name)[0]
        if detected:
            args.extend(["--metadata-set", f"content-type={detected}"])
        self._run(args)
        return StorageFile(id=f"{location.rstrip('/')}/{local_path.name}", name=local_path.name)

    def ensure_folder(self, parent: str, name: str) -> str:
        location = f"{parent.rstrip('/')}/{name}"
        self._run(["mkdir", f"{self.remote}:{location}"])
        return location
