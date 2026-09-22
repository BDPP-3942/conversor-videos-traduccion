from pathlib import Path

import pytest

from src.storage.url import RemoteInputError, URLStorageProvider, validate_remote_url


def test_remote_url_rejects_embedded_credentials():
    with pytest.raises(RemoteInputError):
        validate_remote_url("https://user:pass@example.test/video.mp4")


def test_remote_url_rejects_localhost(monkeypatch):
    monkeypatch.setattr(
        "src.storage.url.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 443))],
    )
    with pytest.raises(RemoteInputError):
        validate_remote_url("https://example.test/video.mp4")


def test_remote_provider_rejects_hls_manifest(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("src.storage.url.local_storage_paths", lambda: {"work": tmp_path})
    monkeypatch.setattr("src.storage.url.validate_remote_url", lambda value: None)

    class Response:
        headers = {"Content-Length": "100", "Content-Type": "application/vnd.apple.mpegurl"}
        _chunks = [b"#EXTM3U"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def geturl(self):
            return "https://example.test/live.m3u8"

        def read(self, size):
            return self._chunks.pop(0) if self._chunks else b""

    class Opener:
        def open(self, request, timeout):
            return Response()

    monkeypatch.setattr("src.storage.url.build_opener", lambda handler: Opener())
    provider = URLStorageProvider("https://example.test/live.m3u8")
    with pytest.raises(RemoteInputError, match="HLS/DASH"):
        provider.list_children("")
    provider.close()
