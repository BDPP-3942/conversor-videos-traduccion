from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path


class RunLock:
    """Small cross-platform exclusive lock for scheduled executions."""

    def __init__(self, path: Path, stale_after_seconds: int = 12 * 3600) -> None:
        self.path = path
        self.stale_after_seconds = stale_after_seconds
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'pid': os.getpid(),
            'host': socket.gethostname(),
            'started_at': int(time.time()),
        }
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if self._is_stale():
                self.path.unlink(missing_ok=True)
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise RuntimeError(
                    f"Another pipeline execution is already running: {self.path}"
                ) from None
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        self.acquired = True
        return self

    def _is_stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
            return age > self.stale_after_seconds
        except FileNotFoundError:
            return False

    def __exit__(self, exc_type, exc, tb):
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False
