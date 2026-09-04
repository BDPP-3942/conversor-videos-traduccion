from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from config.settings import BASE_DIR
from src.hardware import detect_hardware

logger = logging.getLogger(__name__)
MODEL_REPOSITORY = "Prukario/opus-mt-es-en-ct2-int8"
MODEL_REVISION = "ad91ad1697ea1761111ff4c179400796d085b347"
MODEL_LICENSE = "CC-BY-4.0"
MODEL_SIZE_BYTES = 82_500_000
MODEL_MAX_DOWNLOAD_BYTES = 120_000_000
MODEL_FILES = {
    "model.bin": (
        "44c5adc2c680f27c14c991e5ab7f74f38b41597153f7123bc8f6455f09a3b38b",
        79_567_635,
    ),
    "source.spm": (
        "e236ee6d866b635c0142114f8647f39831f9d92534aa2aad75c942f6a78ad0e3",
        825_924,
    ),
    "target.spm": (
        "4dd547c24816a335e7b0b2e63376a8f1b3cbfc671eda5ab808dd44fdadaa8791",
        801_636,
    ),
}
SMALL_MODEL_FILES = {
    "config.json": (1_024, ("decoder_start_token", "eos_token")),
    "shared_vocabulary.json": (4_000_000, ()),
    "tokenizer_config.json": (4_096, ("source_lang", "target_lang")),
}


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
        default_dir = BASE_DIR / "tools" / "models" / "translation" / "opus-mt-es-en-ct2-int8"
        self.model_dir = Path(model_dir or configured or default_dir)

    def status(self) -> LocalModelStatus:
        required = (*MODEL_FILES, *SMALL_MODEL_FILES)
        missing = [name for name in required if not (self.model_dir / name).is_file()]
        if missing:
            return self._unavailable(f"missing files: {', '.join(missing)}")
        if self.model_dir.is_symlink():
            return self._unavailable("managed model directory is a symlink")
        for name, (expected_hash, expected_size) in MODEL_FILES.items():
            path = self.model_dir / name
            if path.is_symlink():
                return self._unavailable(f"symlinked model file: {name}")
            if path.stat().st_size != expected_size:
                return self._unavailable(f"size mismatch: {name}")
            if _sha256(path) != expected_hash:
                return self._unavailable(f"SHA-256 mismatch: {name}")
        for name, (max_size, required_keys) in SMALL_MODEL_FILES.items():
            reason = _validate_small_model_file(self.model_dir / name, max_size, required_keys)
            if reason:
                return self._unavailable(f"invalid metadata: {name}: {reason}")
        return LocalModelStatus(
            True,
            self.model_dir,
            MODEL_REPOSITORY,
            MODEL_REVISION,
            MODEL_SIZE_BYTES,
            MODEL_LICENSE,
        )

    @staticmethod
    def _status(path: Path, reason: str) -> LocalModelStatus:
        return LocalModelStatus(
            False,
            path,
            MODEL_REPOSITORY,
            MODEL_REVISION,
            MODEL_SIZE_BYTES,
            MODEL_LICENSE,
            reason,
        )

    def _unavailable(self, reason: str) -> LocalModelStatus:
        return self._status(self.model_dir, reason)

    def ensure(self, *, confirm: Callable[[LocalModelStatus], bool] | None = None) -> Path:
        status = self.status()
        if status.available:
            return status.path
        if confirm is None or not confirm(status):
            raise RuntimeError(
                f"Local translation model is not ready ({status.reason}). "
                f"Resource: {MODEL_REPOSITORY}@{MODEL_REVISION}; "
                f"approximate size: {MODEL_SIZE_BYTES / 1024**2:.1f} MiB; "
                f"destination: {self.model_dir}; license: {MODEL_LICENSE}. "
                "Prepare it explicitly before offline processing."
            )
        self.download()
        final = self.status()
        if not final.available:
            raise RuntimeError(f"Downloaded local translation model failed validation: {final.reason}")
        return final.path

    def download(self) -> Path:
        if self.model_dir.is_symlink():
            raise RuntimeError(f"Refusing to replace symlinked model directory: {self.model_dir}")
        self.model_dir.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{self.model_dir.name}-", dir=self.model_dir.parent))
        try:
            for name in (*MODEL_FILES, *SMALL_MODEL_FILES):
                url = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}/{name}?download=true"
                max_bytes = min(MODEL_MAX_DOWNLOAD_BYTES, MODEL_FILES.get(name, (0, SMALL_MODEL_FILES[name][0]))[1])
                _download_file(url, temp_dir / name, max_bytes)
            for name, (expected_hash, expected_size) in MODEL_FILES.items():
                path = temp_dir / name
                if path.stat().st_size != expected_size or _sha256(path) != expected_hash:
                    raise RuntimeError(f"Integrity validation failed for downloaded model file: {name}")
            for name, (max_size, required_keys) in SMALL_MODEL_FILES.items():
                reason = _validate_small_model_file(temp_dir / name, max_size, required_keys)
                if reason:
                    raise RuntimeError(f"Integrity validation failed for downloaded metadata: {name}: {reason}")
            metadata = {
                "repository": MODEL_REPOSITORY,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
                "files": MODEL_FILES,
            }
            (temp_dir / "model.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            if self.model_dir.exists():
                if not self.model_dir.is_dir():
                    raise RuntimeError(f"Managed model path is not a directory: {self.model_dir}")
                backup = self.model_dir.with_name(f".{self.model_dir.name}.old")
                if backup.exists() or backup.is_symlink():
                    if backup.is_dir() and not backup.is_symlink():
                        shutil.rmtree(backup)
                    else:
                        backup.unlink()
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
        if self.model_dir.is_symlink():
            raise RuntimeError(f"Refusing to remove symlinked model directory: {self.model_dir}")
        if self.model_dir.exists() and self.model_dir.is_dir():
            shutil.rmtree(self.model_dir)


class LocalTranslationProvider:
    """Offline Spanish→English translation using CTranslate2 + SentencePiece."""

    source_lang = "es"
    target_lang = "en"

    def __init__(self, settings, model_manager: LocalTranslationModelManager | None = None) -> None:
        configured_id = str(getattr(settings, "local_translation_model_id", os.getenv("LOCAL_TRANSLATION_MODEL_ID", MODEL_REPOSITORY)))
        configured_revision = str(
            getattr(settings, "local_translation_model_revision", os.getenv("LOCAL_TRANSLATION_MODEL_REVISION", MODEL_REVISION))
        )
        if configured_id != MODEL_REPOSITORY or configured_revision != MODEL_REVISION:
            raise ValueError("The local translation provider only accepts its pinned model repository and revision")
        self.settings = settings
        model_dir = getattr(settings, "local_translation_model_dir", None)
        self.manager = model_manager or LocalTranslationModelManager(model_dir)
        self.model_path = self.manager.ensure(confirm=self._confirm_download)
        self.device, self.compute_type, self.device_index = self._resolve_runtime()
        try:
            import ctranslate2
            import sentencepiece as spm
        except ImportError as exc:
            raise RuntimeError("Local translation requires ctranslate2 and sentencepiece") from exc
        translator_kwargs = {"device": self.device, "compute_type": self.compute_type}
        if self.device == "cuda":
            translator_kwargs["device_index"] = self.device_index
        self._translator = ctranslate2.Translator(str(self.model_path), **translator_kwargs)
        self._source = spm.SentencePieceProcessor(model_file=str(self.model_path / "source.spm"))
        self._target = spm.SentencePieceProcessor(model_file=str(self.model_path / "target.spm"))

    def _confirm_download(self, status: LocalModelStatus) -> bool:
        return bool(getattr(self.settings, "local_translation_auto_download", os.getenv("LOCAL_TRANSLATION_AUTO_DOWNLOAD", "false").lower() == "true"))

    def _resolve_runtime(self) -> tuple[str, str, int]:
        requested_device = str(getattr(self.settings, "local_translation_device", os.getenv("LOCAL_TRANSLATION_DEVICE", "auto"))).lower().strip()
        requested_compute = str(getattr(self.settings, "local_translation_compute_type", os.getenv("LOCAL_TRANSLATION_COMPUTE_TYPE", "auto"))).lower().strip()
        if requested_device not in {"auto", "cpu", "cuda"}:
            raise ValueError("local_translation_device must be one of: auto, cpu, cuda")
        hardware = detect_hardware()
        detected_gpu = hardware.gpu
        configured_index = getattr(self.settings, "detected_gpu_index", None)
        device_index = max(0, int(configured_index)) if configured_index is not None and int(configured_index) >= 0 else max(0, detected_gpu.device_index or 0)
        if requested_device == "auto":
            requested_device = "cuda" if detected_gpu.usable_for_whisper else "cpu"
            logger.info("Local translation selected %s automatically", requested_device.upper())
        if requested_compute == "auto":
            requested_compute = "float16" if requested_device == "cuda" else "int8"
        if requested_device == "cuda":
            if not detected_gpu.usable_for_whisper:
                logger.warning("Local translation CUDA requested but no verified CTranslate2 CUDA GPU is available; falling back to CPU")
                return "cpu", "int8", 0
            try:
                import ctranslate2
                supported = ctranslate2.get_supported_compute_types("cuda", device_index)
            except (ImportError, AttributeError, RuntimeError, TypeError) as exc:
                logger.warning("Local translation CUDA capability check failed; falling back to CPU: %s", exc)
                return "cpu", "int8", 0
            if requested_compute not in supported:
                if "float16" in supported:
                    requested_compute = "float16"
                elif "int8_float16" in supported:
                    requested_compute = "int8_float16"
                elif supported:
                    requested_compute = sorted(supported)[0]
                else:
                    return "cpu", "int8", 0
        return requested_device, requested_compute, device_index

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        tokens = [self._source.encode(text, out_type=str) + ["</s>"] for text in texts]
        beam_size = max(1, int(getattr(self.settings, "local_translation_beam_size", os.getenv("LOCAL_TRANSLATION_BEAM_SIZE", 2))))
        results = self._translator.translate_batch(tokens, beam_size=beam_size)
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


def _validate_small_model_file(path: Path, max_size: int, required_keys: tuple[str, ...]) -> str:
    if path.is_symlink():
        return "symlink is not allowed"
    try:
        size = path.stat().st_size
    except OSError as exc:
        return f"cannot stat file: {exc}"
    if size > max_size:
        return f"size exceeds {max_size} bytes"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return f"invalid UTF-8 JSON: {exc}"
    if not isinstance(data, dict):
        return "root must be a JSON object"
    missing = [key for key in required_keys if key not in data]
    if missing:
        return f"missing keys: {', '.join(missing)}"
    return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_file(url: str, destination: Path, max_bytes: int) -> None:
    if not url.startswith("https://huggingface.co/"):
        raise ValueError("Model downloads are restricted to the pinned Hugging Face origin")
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "video-translation-pipeline/1.5"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            resumed = offset > 0 and getattr(response, "status", None) == 206
            if not resumed:
                offset = 0
                partial.unlink(missing_ok=True)
            length = response.headers.get("Content-Length")
            expected = offset + int(length) if length else None
            if expected and expected > max_bytes:
                raise RuntimeError(f"Refusing oversized model download: {expected} bytes")
            mode = "ab" if resumed else "wb"
            written = offset
            with partial.open(mode) as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise RuntimeError("Model download exceeded the configured size limit")
                    handle.write(chunk)
            partial.replace(destination)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Model download failed: {exc}") from exc
