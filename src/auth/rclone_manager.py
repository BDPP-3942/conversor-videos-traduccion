from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RCLONE_VERSION = "1.75.0"
RCLONE_DOWNLOAD_BASE = "https://github.com/rclone/rclone/releases/download/v{version}"
RCLONE_RELEASE_BASE = "https://downloads.rclone.org/v{version}"


class RcloneManager:
    """Owns the rclone executable and its configuration without requiring system installation."""

    def __init__(self, binary_path: Path, config_file: Path) -> None:
        self.binary_path = binary_path
        self.config_file = config_file

    def ensure_binary(self) -> Path:
        if self.binary_path.is_file():
            self._chmod_executable()
            return self.binary_path
        self.binary_path.parent.mkdir(parents=True, exist_ok=True)
        self._download_binary()
        self._chmod_executable()
        self.version()
        return self.binary_path

    def version(self) -> str:
        result = self._run(["version"], check=True)
        first = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return first.strip()

    def list_remotes(self) -> list[str]:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists() or not self.binary_path.is_file():
            return []
        result = self._run(["listremotes"], check=True)
        return sorted(line.strip().rstrip(":") for line in result.stdout.splitlines() if line.strip())

    def healthcheck(self, remote: str, location: str = "") -> dict[str, object]:
        """Perform a read-only remote listing.

        For OAuth-backed backends this is also the point where rclone can refresh
        an expired access token and persist the refreshed token in rclone.conf.
        """
        self.ensure_binary()
        target = f"{remote}:{location.strip('/')}" if location.strip("/") else f"{remote}:"
        result = self._run(["lsjson", target, "--max-depth", "1"], check=False, timeout=120)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "rclone remote healthcheck failed").strip()
            raise RuntimeError(detail)
        try:
            items = json.loads(result.stdout or "[]")
            item_count = len(items) if isinstance(items, list) else 0
        except json.JSONDecodeError:
            item_count = 0
        return {"remote": remote, "location": location, "items": item_count, "healthy": True}

    def check_for_update(self) -> str:
        self.ensure_binary()
        result = self._run(["selfupdate", "--check"], check=True, timeout=180)
        return result.stdout.strip()

    def self_update(self) -> str:
        self.ensure_binary()
        result = self._run(["selfupdate", "--stable"], check=True, timeout=300)
        return result.stdout.strip()

    def delete_remote(self, name: str) -> None:
        self.ensure_binary()
        self._run(["config", "delete", name], check=True)

    def config_interactive(self, *, name: str | None = None, backend: str | None = None) -> None:
        """Start rclone's native wizard while still keeping its config isolated in the project."""
        self.ensure_binary()
        args = ["config"]
        if name and backend:
            args += ["create", name, backend]
        subprocess.run(self._base_command(args), check=True)

    def config_create_non_interactive(self, name: str, backend: str, options: dict[str, str] | None = None) -> dict:
        """Create a remote using rclone's machine-friendly question/continue protocol."""
        self.ensure_binary()
        options = options or {}
        args = ["config", "create", name, backend, "--non-interactive"]
        for key, value in options.items():
            args.extend([key, value])
        result = self._run(args, check=False)
        return self._decode_protocol(result.stdout, result.stderr)

    def config_continue(self, name: str, state: str, result_value: str) -> dict:
        self.ensure_binary()
        result = self._run(
            [
                "config",
                "update",
                name,
                "--continue",
                "--state",
                state,
                "--result",
                result_value,
                "--non-interactive",
            ],
            check=False,
        )
        return self._decode_protocol(result.stdout, result.stderr)

    def authorize(self, backend: str, *authorize_args: str) -> str:
        self.ensure_binary()
        result = self._run(["authorize", backend, *authorize_args], check=True)
        return result.stdout.strip()

    def _base_command(self, args: list[str]) -> list[str]:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        return [str(self.binary_path), "--config", str(self.config_file), *args]

    def _run(self, args: list[str], *, check: bool, timeout: int = 300) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                self._base_command(args),
                capture_output=True,
                text=True,
                check=check,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Managed rclone executable is missing") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("rclone command timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "rclone failed").strip()
            raise RuntimeError(detail) from exc

    @staticmethod
    def _decode_protocol(stdout: str, stderr: str) -> dict:
        for text in (stdout, stderr):
            for line in text.splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {"State": "", "Output": stdout.strip(), "Error": stderr.strip()}

    def _download_binary(self) -> None:
        asset = _asset_name(RCLONE_VERSION)
        archive_url = f"{RCLONE_DOWNLOAD_BASE.format(version=RCLONE_VERSION)}/{asset}"
        checksum_url = f"{RCLONE_RELEASE_BASE.format(version=RCLONE_VERSION)}/SHA256SUMS"
        with tempfile.TemporaryDirectory(prefix="rclone-bootstrap-") as temp_dir:
            temp = Path(temp_dir)
            archive = temp / asset
            checksums = temp / "SHA256SUMS"
            _download(archive_url, archive)
            _download(checksum_url, checksums)
            expected = _checksum_for_asset(checksums, asset)
            actual = _sha256(archive)
            if expected.lower() != actual.lower():
                raise RuntimeError("rclone download checksum verification failed")
            with zipfile.ZipFile(archive) as handle:
                matches = [
                    name for name in handle.namelist() if name.endswith("/rclone") or name.endswith("/rclone.exe")
                ]
                if len(matches) != 1:
                    raise RuntimeError("Unexpected rclone archive contents")
                extracted = temp / Path(matches[0]).name
                with handle.open(matches[0]) as source, extracted.open("wb") as target:
                    shutil.copyfileobj(source, target)
                os.replace(extracted, self.binary_path)

    def _chmod_executable(self) -> None:
        if os.name != "nt":
            try:
                self.binary_path.chmod(self.binary_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError:
                pass


def _asset_name(version: str) -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        os_name = "windows"
    elif system == "darwin":
        os_name = "osx"
    elif system == "linux":
        os_name = "linux"
    else:
        raise RuntimeError(f"Unsupported operating system for managed rclone: {system}")

    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "386",
        "i686": "386",
    }
    arch = arch_map.get(machine)
    if not arch:
        raise RuntimeError(f"Unsupported CPU architecture for managed rclone: {machine}")
    return f"rclone-v{version}-{os_name}-{arch}.zip"


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "video-translation-pipeline/3"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _checksum_for_asset(checksums_path: Path, asset: str) -> str:
    for line in checksums_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and Path(parts[-1]).name == asset:
            return parts[0]
    raise RuntimeError(f"Checksum for rclone asset not found: {asset}")
