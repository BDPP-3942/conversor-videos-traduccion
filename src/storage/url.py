from __future__ import annotations

import hashlib
import ipaddress
import re
import shutil
import socket
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.runtime_paths import local_storage_paths
from src.storage.base import StorageFile, StorageProvider

MAX_REMOTE_DOWNLOAD_BYTES = 10 * 1024**3
REMOTE_TIMEOUT_SECONDS = 120
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_BLOCKED_SUFFIXES = {'.m3u8', '.mpd'}

class RemoteInputError(RuntimeError):
    """Indica que un recurso remoto no puede utilizarse como entrada segura."""

def validate_remote_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme.lower() not in {'http', 'https'}:
        raise RemoteInputError('Solo se admiten URLs HTTP(S) como entrada remota.')
    if not parsed.hostname:
        raise RemoteInputError('La URL remota debe incluir un hostname.')
    if parsed.username or parsed.password:
        raise RemoteInputError('No se permiten credenciales incrustadas en una URL remota.')
    host = parsed.hostname.strip().lower()
    if host in {'localhost', 'localhost.localdomain'} or host.endswith('.local'):
        raise RemoteInputError('No se permiten nombres de host de red local como entrada remota.')
    try:
        addresses = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(host, 443 if parsed.scheme.lower() == 'https' else 80)}
    except OSError as exc:
        raise RemoteInputError(f'No se puede resolver el host remoto: {host}') from exc
    if any(not address.is_global for address in addresses):
        raise RemoteInputError('La entrada remota solo puede resolver a direcciones IP públicas.')

class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        validate_remote_url(target)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class URLStorageProvider(StorageProvider):
    """Materializa una URL HTTP(S) en un temporal aislado para el pipeline existente."""
    def __init__(self, url: str, *, max_bytes: int = MAX_REMOTE_DOWNLOAD_BYTES, timeout: int = REMOTE_TIMEOUT_SECONDS) -> None:
        validate_remote_url(url)
        self.url = url
        self.max_bytes = max(1, int(max_bytes))
        self.timeout = max(1, int(timeout))
        work = local_storage_paths()['work']
        work.mkdir(parents=True, exist_ok=True)
        self._tempdir = tempfile.TemporaryDirectory(prefix='remote-input-', dir=work)
        self._downloaded: Path | None = None

    def _ensure_downloaded(self) -> Path:
        if self._downloaded is not None and self._downloaded.is_file(): return self._downloaded
        opener = build_opener(_SafeRedirectHandler())
        request = Request(self.url, headers={'User-Agent': 'VideoTranslationPipeline/1.0'}, method='GET')
        try:
            with opener.open(request, timeout=self.timeout) as response:
                final_url = response.geturl()
                validate_remote_url(final_url)
                suffix = Path(urlparse(final_url).path).suffix.lower()
                if suffix in _BLOCKED_SUFFIXES: raise RemoteInputError('No se admiten manifiestos HLS/DASH porque el pipeline requiere un vídeo o ZIP materializado.')
                filename = self._filename(response.headers.get('Content-Disposition', ''), final_url, response.headers.get('Content-Type', ''))
                destination = Path(self._tempdir.name) / filename
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        if int(content_length) > self.max_bytes: raise RemoteInputError('La entrada remota supera el límite de descarga configurado.')
                    except ValueError: pass
                total = 0
                with destination.open('wb') as handle:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                        if not chunk: break
                        total += len(chunk)
                        if total > self.max_bytes: raise RemoteInputError('La entrada remota supera el límite de descarga configurado.')
                        handle.write(chunk)
        except RemoteInputError: raise
        except OSError as exc: raise RemoteInputError(f'Ha fallado la descarga remota: {type(exc).__name__}: {exc}') from exc
        if not destination.is_file() or destination.stat().st_size == 0: raise RemoteInputError('El recurso remoto está vacío.')
        self._downloaded = destination
        return destination

    @staticmethod
    def _filename(content_disposition: str, url: str, content_type: str = '') -> str:
        match = re.search(r"filename\\*?=(?:UTF-8''|\"|')?([^;\"']+)", content_disposition, re.IGNORECASE)
        if match: candidate = Path(match.group(1).strip()).name
        else: candidate = Path(urlparse(url).path).name
        if not candidate:
            media_type = content_type.split(';', 1)[0].strip().lower()
            candidate = {'application/zip':'remote-input.zip','video/mp4':'remote-input.mp4','video/webm':'remote-input.webm','video/quicktime':'remote-input.mov','video/x-matroska':'remote-input.mkv'}.get(media_type, 'remote-input.bin')
        return 'remote-input.bin' if candidate in {'.', '..'} else candidate

    def list_zip_files(self, location: str) -> list[StorageFile]:
        del location
        downloaded = self._ensure_downloaded()
        return [StorageFile(id=str(downloaded), name=downloaded.name)] if downloaded.suffix.lower() == '.zip' else []

    def list_children(self, parent: str) -> list[StorageFile]:
        del parent
        downloaded = self._ensure_downloaded()
        return [StorageFile(id=str(downloaded), name=downloaded.name)]

    def download_file(self, file: StorageFile, destination: Path) -> None:
        source = Path(file.id)
        if not source.is_file(): raise FileNotFoundError(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        raise RuntimeError('Una URL HTTP(S) no puede utilizarse como destino.')

    def ensure_folder(self, parent: str, name: str) -> str:
        raise RuntimeError('Una URL HTTP(S) no puede utilizarse como destino.')

    def source_fingerprint(self, file: StorageFile) -> dict[str, object]:
        digest = hashlib.sha256()
        with Path(file.id).open('rb') as handle:
            for chunk in iter(lambda: handle.read(DOWNLOAD_CHUNK_BYTES), b''): digest.update(chunk)
        path = Path(file.id)
        return {'sha256': digest.hexdigest(), 'size': path.stat().st_size}

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        del file, status, output_folders

    def close(self) -> None:
        self._tempdir.cleanup()
