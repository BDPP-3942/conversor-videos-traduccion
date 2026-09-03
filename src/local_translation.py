from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

MODEL_REPOSITORY = "Prukario/opus-mt-es-en-ct2-int8"
MODEL_REVISION = "ad91ad1697ea1761111ff4c179400796d085b347"
MODEL_LICENSE = "CC-BY-4.0"
MODEL_SIZE_BYTES = 82_500_000
MODEL_MAX_DOWNLOAD_BYTES = 120_000_000
MODEL_FILES = {
    "model.bin": ("44c5adc2c680f27c14c991e5ab7f74f38b41597153f7123bc8f6455f09a3b38b", 79_567_635),
    "source.spm": ("e236ee6d866b635c0142114f8647f39831f9d92534aa2aad75c942f6a78ad0e3", 825_924),
    "target.spm": ("4dd547c24816a335e7b0b2e63376a8f1b3cbfc671eda5ab808dd44fdadaa8791", 801_636),
}
SMALL_MODEL_FILES = ("config.json", "shared_vocabulary.json", "tokenizer_config.json")


@dataclass(frozen=True)
class LocalModelStatus:
    available: bool
    path: Path
    repository: str
    revision: str
    expected_size_bytes: int
    license: str
    reason: str = ""


class LocalTranslationModelManager:
    """Manage a pinned, offline-capable CTranslate2 translation model."""

    def __init__(self, model_dir: Path | None = None) -> None:
        configured = os.getenv("LOCAL_TRANSLATION_MODEL_DIR", "").strip()
        self.model_dir = Path(model_dir or configured or (BASE_DIR / "tools" / "models" / "translation" / "opus-mt-es-en-ct2-int8"))

    def status(self) -> LocalModelStatus:
        missing = [name for name in MODEL_FILES if not (self.model_dir / name).is_file()]
        if missing:
            return LocalModelStatus(False, self.model_dir, MODEL_REPOSITORY, MODEL_REVISION, MODEL_SIZE_BYTES, MODEL_LICENSE, f"missing files: {', '.join(missing)}")
        for name, (expected_hash, expected_size) in MODEL_FILES.items():
            path = self.model_dir / name
            if path.stat().st_size != expected_size:
                return LocalModelStatus(False, self.model_dir, MODEL_REPOSITORY, MODEL_REVISION, MODEL_SIZE_BYTES, MODEL_LICENSE, f"size mismatch: {name}")
            if _sha256(path) != expected_hash:
                return LocalModelStatus(False, self.model_dir, MODEL_REPOSITORY, MODEL_REVISION, MODEL_SIZE_BYTES, MODEL_LICENSE, f"SHA-256 mismatch: {name}")
        return LocalModelStatus(True, self.model_dir, MODEL_REPOSITORY, MODEL_REVISION, MODEL_SIZE_BYTES, MODEL_LICENSE)

    def ensure(self, *, confirm: Callable[[LocalModelStatus], bool] | None = None) -> Path:
        status = self.status()
        if status.available:
            return status.path
        if confirm is None or not confirm(status):
            raise RuntimeError(
                f"Local translation model is not ready ({status.reason}). "
                f"Resource: {MODEL_REPOSITORY}@{MODEL_REVISION}; approximate size: {MODEL_SIZE_BYTES / 1024**2:.1f} MiB; "
                f"destination: {self.model_dir}; license: {MODEL_LICENSE}. "
                "Prepare it explicitly before offline processing."
            )
        self.download()
        final = self.status()
        if not final.available:
            raise RuntimeError(f"Downloaded local translation model failed validation: {final.reason}")
        return final.path

    def download(self) -> Path:
        self.model_dir.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{self.model_dir.name}-", dir=self.model_dir.parent))
        try:
            for name in (*MODEL_FILES, *SMALL_MODEL_FILES):
                url = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}/{name}?download=true"
                destination = temp_dir / name
                _download_file(url, destination, MODEL_MAX_DOWNLOAD_BYTES)
            for name, (expected_hash, expected_size) in MODEL_FILES.items():
                path = temp_dir / name
                if path.stat().st_size != expected_size or _sha256(path) != expected_hash:
                    raise RuntimeError(f"Integrity validation failed for downloaded model file: {name}")
            marker = temp_dir / "model.json"
            marker.write_text(
                json.dumps(
                    {
                        "repository": MODEL_REPOSITORY,
                        "revision": MODEL_REVISION,
                        "license": MODEL_LICENSE,
                        "files": MODEL_FILES,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            if self.model_dir.exists():
                backup = self.model_dir.with_name(f".{self.model_dir.name}.old")
                if backup.exists():
                    shutil.rmtree(backup)
                self.model_dir.replace(backup)
                try:
                    temp_dir.replace(self.model_dir)
                except Exception:
                    backup.replace(self.model_dir)
                    raise
                shutil.rmtree(backup)
            else:
                temp_dir.replace(self.model_dir)
            return self.model_dir
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def cleanup(self) -> None:
        if self.model_dir.exists() and self.model_dir.is_dir():
            shutil.rmtree(self.model_dir)


class LocalTranslationProvider:
    """Offline Spanish→English translation using CTranslate2 + SentencePiece."""

    source_lang = "es"
    target_lang = "en"

    def __init__(self, settings, model_manager: LocalTranslationModelManager | None = None) -> None:
        self.settings = settings
        self.manager = model_manager or LocalTranslationModelManager()
        self.model_path = self.manager.ensure(confirm=self._confirm_download)
        self.device, self.compute_type = self._resolve_runtime()
        try:
            import ctranslate2
            import sentencepiece as spm
        except ImportError as exc:
            raise RuntimeError("Local translation requires ctranslate2 and sentencepiece") from exc
        self._translator = ctranslate2.Translator(
            str(self.model_path), device=self.device, compute_type=self.compute_type
        )
        self._source = spm.SentencePieceProcessor(model_file=str(self.model_path / "source.spm"))
        self._target = spm.SentencePieceProcessor(model_file=str(self.model_path / "target.spm"))

    def _confirm_download(self, status: LocalModelStatus) -> bool:
        if os.getenv("LOCAL_TRANSLATION_AUTO_DOWNLOAD", "false").strip().lower() != "true":
            return False
        if not hasattr(__import__("builtins"), "input"):
            return False
        answer = input(
            f"Local translation model {status.repository}@{status.revision} is missing. "
            f"Download ~{status.expected_size_bytes / 1024**2:.1f} MiB to {status.path}? [y/N] "
        ).strip().lower()
        return answer in {"y", "yes"}

    def _resolve_runtime(self) -> tuple[str, str]:
        requested_device = str(getattr(self.settings, "local_translation_device", "auto")).lower().strip()
        requested_compute = str(getattr(self.settings, "local_translation_compute_type", "auto")).lower().strip()
        if requested_device not in {"auto", "cpu", "cuda"}:
            raise ValueError("local_translation_device must be one of: auto, cpu, cuda")
        if requested_compute == "auto":
            requested_compute = "int8" if requested_device != "cuda" else "float16"
        if requested_device == "cuda":
            try:
                import ctranslate2
                supported = ctranslate2.get_supported_compute_types("cuda", int(getattr(self.settings, "detected_gpu_index", 0)))
                if not supported:
                    raise RuntimeError("CTranslate2 reports no supported CUDA compute types for local translation")
            except (ImportError, AttributeError, RuntimeError, TypeError) as exc:
                logger.warning("Local translation CUDA unavailable; falling back to CPU: %s", exc)
                return "cpu", "int8"
            return "cuda", requested_compute
        return "cpu", requested_compute

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        tokens = [self._source.encode(text, out_type=str) + ["</s>"] for text in texts]
        results = self._translator.translate_batch(
            tokens,
            beam_size=max(1, int(getattr(self.settings, "local_translation_beam_size", 2))),
        )
        outputs: list[str] = []
        for result in results:
            hypotheses = getattr(result, "hypotheses", None) or []
            if not hypotheses:
                outputs.append("")
                continue
            tokens_out = list(hypotheses[0])
            if "</s>" in tokens_out:
                tokens_out = tokens_out[: tokens_out.index("</s>")]
            outputs.append(self._target.decode(tokens_out).strip())
        if len(outputs) != len(texts):
            raise RuntimeError(f"Local translation returned {len(outputs)} results for {len(texts)} inputs")
        return outputs


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_file(url: str, destination: Path, max_bytes: int) -> None:
    if not url.startswith("https://huggingface.co/"):
        raise ValueError("Model downloads are restricted to the pinned Hugging Face origin")
    request = urllib.request.Request(url, headers={"User-Agent": "video-translation-pipeline/1.5"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise RuntimeError(f"Refusing oversized model download: {length} bytes")
            written = 0
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise RuntimeError("Model download exceeded the configured size limit")
                    handle.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Model download failed: {exc}") from exc
