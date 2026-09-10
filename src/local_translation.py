from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from config.settings import BASE_DIR
from src.hardware import detect_hardware

logger = logging.getLogger(__name__)

# MADLAD-400 3B is the quality-oriented offline default. This CTranslate2
# INT8 conversion is Apache-2.0 and keeps the model below the 3 GB disk budget.
MODEL_REPOSITORY = "cstr/madlad400-3b-ct2-int8"
MODEL_REVISION = "12eff26f7d93623e2b2d3b5345e5863e14599dae"
MODEL_LICENSE = "Apache-2.0"
MODEL_SIZE_BYTES = 2_950_208_290
MODEL_MAX_DOWNLOAD_BYTES = 3_000_000_000
MODEL_MAX_TOTAL_BYTES = 3_000_000_000
MODEL_DOWNLOAD_WORKSPACE_BYTES = MODEL_SIZE_BYTES * 2 + 100_000_000
MODEL_FILES = {
    "model.bin": (
        "890ed3b7e4654dcf1b9e7f2ce6ce641447462e782881e81aac443568eb1ca702",
        2_950_208_290,
    ),
    "sentencepiece.model": (
        "ef11ac9a22c7503492f56d48dce53be20e339b63605983e9f27d2cd0e0f3922c",
        4_427_844,
    ),
}
SMALL_MODEL_FILES = {
    "config.json": (4_096, ("decoder_start_token", "eos_token")),
    "shared_vocabulary.json": (20_000_000, ()),
}
REQUIRED_FILES = (*MODEL_FILES, *SMALL_MODEL_FILES)


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
    """Manage the pinned, offline-capable MADLAD CTranslate2 model."""

    def __init__(self, model_dir: Path | None = None) -> None:
        configured = os.getenv("LOCAL_TRANSLATION_MODEL_DIR", "").strip()
        default_dir = BASE_DIR / "tools" / "models" / "translation" / "madlad400-3b-ct2-int8"
        self.model_dir = Path(model_dir or configured or default_dir)

    @property
    def download_dir(self) -> Path:
        return self.model_dir.with_name(f".{self.model_dir.name}.download")

    @property
    def huggingface_token(self) -> str | None:
        token = os.getenv("LOCAL_TRANSLATION_HF_TOKEN", "").strip()
        if not token:
            token = os.getenv("HF_TOKEN", "").strip()
        return token or None

    def status(self) -> LocalModelStatus:
        missing = [name for name in REQUIRED_FILES if not (self.model_dir / name).is_file()]
        if missing:
            return self._unavailable(f"missing files: {', '.join(missing)}")
        if self.model_dir.is_symlink():
            return self._unavailable("managed model directory is a symlink")
        total_size = 0
        for name, (expected_hash, expected_size) in MODEL_FILES.items():
            path = self.model_dir / name
            if path.is_symlink():
                return self._unavailable(f"symlinked model file: {name}")
            size = path.stat().st_size
            total_size += size
            if size != expected_size:
                return self._unavailable(f"size mismatch: {name}")
            if _sha256(path) != expected_hash:
                return self._unavailable(f"SHA-256 mismatch: {name}")
        for name, (max_size, required_keys) in SMALL_MODEL_FILES.items():
            path = self.model_dir / name
            total_size += path.stat().st_size
            reason = _validate_small_model_file(path, max_size, required_keys)
            if reason:
                return self._unavailable(f"invalid metadata: {name}: {reason}")
        if total_size > MODEL_MAX_TOTAL_BYTES:
            return self._unavailable(
                f"model exceeds {MODEL_MAX_TOTAL_BYTES} byte installation budget: {total_size} bytes"
            )
        return LocalModelStatus(
            True,
            self.model_dir,
            MODEL_REPOSITORY,
            MODEL_REVISION,
            MODEL_SIZE_BYTES,
            MODEL_LICENSE,
        )

    def _unavailable(self, reason: str) -> LocalModelStatus:
        return LocalModelStatus(
            False,
            self.model_dir,
            MODEL_REPOSITORY,
            MODEL_REVISION,
            MODEL_SIZE_BYTES,
            MODEL_LICENSE,
            reason,
        )

    def ensure(self, *, confirm: Callable[[LocalModelStatus], bool] | None = None) -> Path:
        status = self.status()
        if status.available:
            return status.path
        if confirm is None or not confirm(status):
            workspace_mib = MODEL_DOWNLOAD_WORKSPACE_BYTES / 1024**2
            raise RuntimeError(
                f"Local translation model is not ready ({status.reason}). "
                f"Resource: {MODEL_REPOSITORY}@{MODEL_REVISION}; "
                f"model size: {MODEL_SIZE_BYTES / 1_000_000:.0f} MB; "
                f"temporary download workspace: about {workspace_mib:.0f} MiB; "
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
        download_dir = self.download_dir
        if download_dir.is_symlink():
            raise RuntimeError(f"Refusing to use symlinked model download directory: {download_dir}")
        if download_dir.exists() and not download_dir.is_dir():
            raise RuntimeError(f"Model download path is not a directory: {download_dir}")
        download_dir.mkdir(parents=True, exist_ok=True)
        try:
            for name in REQUIRED_FILES:
                url = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}/{name}?download=true"
                limit = MODEL_FILES[name][1] if name in MODEL_FILES else SMALL_MODEL_FILES[name][0]
                _download_file(url, download_dir / name, min(MODEL_MAX_DOWNLOAD_BYTES, limit), self.huggingface_token)
            for name, (expected_hash, expected_size) in MODEL_FILES.items():
                path = download_dir / name
                if path.stat().st_size != expected_size or _sha256(path) != expected_hash:
                    raise RuntimeError(f"Integrity validation failed for downloaded model file: {name}")
            for name, (max_size, required_keys) in SMALL_MODEL_FILES.items():
                reason = _validate_small_model_file(download_dir / name, max_size, required_keys)
                if reason:
                    raise RuntimeError(f"Integrity validation failed for downloaded metadata: {name}: {reason}")
            total_size = sum((download_dir / name).stat().st_size for name in REQUIRED_FILES)
            if total_size > MODEL_MAX_TOTAL_BYTES:
                raise RuntimeError(f"Downloaded model exceeds 3 GB installation budget: {total_size} bytes")
            metadata = {
                "repository": MODEL_REPOSITORY,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
                "expected_size_bytes": MODEL_SIZE_BYTES,
                "files": {
                    name: {"sha256": expected_hash, "size": expected_size}
                    for name, (expected_hash, expected_size) in MODEL_FILES.items()
                },
            }
            (download_dir / "model.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
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
                    download_dir.replace(self.model_dir)
                except Exception:
                    backup.replace(self.model_dir)
                    raise
                shutil.rmtree(backup)
            else:
                download_dir.replace(self.model_dir)
            return self.model_dir
        except Exception:
            logger.warning("Local translation model download interrupted or failed; partial files were preserved")
            raise

    def cleanup(self) -> None:
        if self.model_dir.is_symlink():
            raise RuntimeError(f"Refusing to remove symlinked model directory: {self.model_dir}")
        if self.model_dir.exists() and self.model_dir.is_dir():
            shutil.rmtree(self.model_dir)
        if self.download_dir.is_symlink():
            raise RuntimeError(f"Refusing to remove symlinked model download directory: {self.download_dir}")
        if self.download_dir.exists() and self.download_dir.is_dir():
            shutil.rmtree(self.download_dir)


class LocalTranslationProvider:
    """Offline Spanish→English translation using MADLAD, CTranslate2 and SentencePiece."""

    source_lang = "es"
    target_lang = "en"

    def __init__(self, settings, model_manager: LocalTranslationModelManager | None = None) -> None:
        configured_id = str(
            getattr(settings, "local_translation_model_id", os.getenv("LOCAL_TRANSLATION_MODEL_ID", MODEL_REPOSITORY))
        )
        configured_revision = str(
            getattr(
                settings,
                "local_translation_model_revision",
                os.getenv("LOCAL_TRANSLATION_MODEL_REVISION", MODEL_REVISION),
            )
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
        self._tokenizer = spm.SentencePieceProcessor(model_file=str(self.model_path / "sentencepiece.model"))

    def _confirm_download(self, status: LocalModelStatus) -> bool:
        return bool(
            getattr(
                self.settings,
                "local_translation_auto_download",
                os.getenv("LOCAL_TRANSLATION_AUTO_DOWNLOAD", "false").lower() == "true",
            )
        )

    def _resolve_runtime(self) -> tuple[str, str, int]:
        requested_device = str(
            getattr(self.settings, "local_translation_device", os.getenv("LOCAL_TRANSLATION_DEVICE", "auto"))
        ).lower().strip()
        requested_compute = str(
            getattr(
                self.settings,
                "local_translation_compute_type",
                os.getenv("LOCAL_TRANSLATION_COMPUTE_TYPE", "auto"),
            )
        ).lower().strip()
        if requested_device not in {"auto", "cpu", "cuda"}:
            raise ValueError("local_translation_device must be one of: auto, cpu, cuda")
        hardware = detect_hardware()
        detected_gpu = hardware.gpu
        configured_index = getattr(self.settings, "detected_gpu_index", None)
        device_index = (
            max(0, int(configured_index))
            if configured_index is not None and int(configured_index) >= 0
            else max(0, detected_gpu.device_index or 0)
        )
        if requested_device == "auto":
            requested_device = "cuda" if detected_gpu.usable_for_whisper else "cpu"
            logger.info("Local translation selected %s automatically", requested_device.upper())
        if requested_compute == "auto":
            requested_compute = "float16" if requested_device == "cuda" else "int8"
        if requested_device == "cuda":
            if not detected_gpu.usable_for_whisper:
                logger.warning("Local translation CUDA requested but no verified GPU is available; falling back to CPU")
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
        target_prefix = f"<2{self.target_lang}>"
        tokens = [self._tokenizer.encode(f"{target_prefix} {text}", out_type=str) for text in texts]
        beam_size = max(
            1,
            int(getattr(self.settings, "local_translation_beam_size", os.getenv("LOCAL_TRANSLATION_BEAM_SIZE", 2))),
        )
        results = self._translator.translate_batch(
            tokens,
            batch_type="tokens",
            beam_size=beam_size,
            no_repeat_ngram_size=1,
        )
        outputs: list[str] = []
        for result in results:
            hypotheses = getattr(result, "hypotheses", None) or []
            outputs.append(self._tokenizer.decode(list(hypotheses[0])).strip() if hypotheses else "")
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
    if required_keys and not isinstance(data, dict):
        return "root must be a JSON object"
    if required_keys:
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


def _download_file(url: str, destination: Path, max_bytes: int, auth_token: str | None = None) -> None:
    parsed = urllib.parse.urlsplit(url)
    prefix = f"/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}/"
    if parsed.scheme != "https" or parsed.netloc != "huggingface.co" or not parsed.path.startswith(prefix):
        raise ValueError("Model downloads are restricted to the pinned Hugging Face origin and revision")
    filename = parsed.path.removeprefix(prefix)
    if not filename or "/" in filename:
        raise ValueError("Model download path is not a valid repository file")
    cache_dir = Path(tempfile.mkdtemp(prefix="video-translation-hf-cache-"))
    try:
        try:
            from huggingface_hub import hf_hub_download

            cached = Path(
                hf_hub_download(
                    repo_id=MODEL_REPOSITORY,
                    filename=filename,
                    revision=MODEL_REVISION,
                    token=auth_token,
                    cache_dir=cache_dir,
                )
            )
        except Exception as exc:
            hint = (
                " Configure LOCAL_TRANSLATION_HF_TOKEN (or HF_TOKEN) if the Hub/Xet endpoint requires authentication."
                if auth_token is None
                else " Verify that the configured Hugging Face token has read access to the pinned repository."
            )
            raise RuntimeError(f"Hugging Face model download failed: {exc}.{hint}") from exc
        size = cached.stat().st_size
        if size > max_bytes:
            raise RuntimeError(f"Refusing oversized model download: {size} bytes")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cached, destination)
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
