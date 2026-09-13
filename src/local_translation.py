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

# The project keeps both local translation engines available. MADLAD is the
# preferred quality-oriented model; OPUS-MT remains a small compatibility and
# low-disk fallback model instead of being replaced or discarded.
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

OPUS_MODEL_NAME = "opus-mt-es-en-ct2-int8"
OPUS_MODEL_REPOSITORY = "Prukario/opus-mt-es-en-ct2-int8"
OPUS_MODEL_REVISION = "ad91ad1697ea1761111ff4c179400796d085b347"
OPUS_MODEL_LICENSE = "CC-BY-4.0"
OPUS_MODEL_SIZE_BYTES = 82_500_000
OPUS_MODEL_MAX_DOWNLOAD_BYTES = 120_000_000
OPUS_MODEL_FILES = {
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
OPUS_SMALL_MODEL_FILES = {
    "config.json": (1_024, ("decoder_start_token", "eos_token")),
    "shared_vocabulary.json": (4_000_000, ()),
    "tokenizer_config.json": (4_096, ("source_lang", "target_lang")),
}
OPUS_BUNDLED_MODEL_FILES = ("config.json", "tokenizer_config.json")

MODEL_ALIASES = {
    "madlad": "madlad400-3b-ct2-int8",
    "madlad400": "madlad400-3b-ct2-int8",
    "madlad400-3b-ct2-int8": "madlad400-3b-ct2-int8",
    "opus": OPUS_MODEL_NAME,
    "opus_mt": OPUS_MODEL_NAME,
    "opus-mt": OPUS_MODEL_NAME,
    OPUS_MODEL_NAME: OPUS_MODEL_NAME,
}
DEFAULT_MODEL_NAME = "madlad400-3b-ct2-int8"


@dataclass(frozen=True)
class LocalModelDefinition:
    name: str
    repository: str
    revision: str
    license: str
    expected_size_bytes: int
    max_download_bytes: int
    max_total_bytes: int
    model_files: dict[str, tuple[str, int]]
    small_model_files: dict[str, tuple[int, tuple[str, ...]]]
    bundled_model_files: tuple[str, ...] = ()
    tokenizer_kind: str = "madlad"


@dataclass(frozen=True)
class LocalModelStatus:
    available: bool
    path: Path
    repository: str
    revision: str
    expected_size_bytes: int
    license: str
    model_name: str = DEFAULT_MODEL_NAME
    reason: str = ""


def _definition(model_name: str) -> LocalModelDefinition:
    normalized = MODEL_ALIASES.get(model_name.strip().lower(), model_name.strip().lower())
    if normalized == OPUS_MODEL_NAME:
        return LocalModelDefinition(
            OPUS_MODEL_NAME,
            OPUS_MODEL_REPOSITORY,
            OPUS_MODEL_REVISION,
            OPUS_MODEL_LICENSE,
            OPUS_MODEL_SIZE_BYTES,
            OPUS_MODEL_MAX_DOWNLOAD_BYTES,
            OPUS_MODEL_SIZE_BYTES + 10_000_000,
            OPUS_MODEL_FILES,
            OPUS_SMALL_MODEL_FILES,
            OPUS_BUNDLED_MODEL_FILES,
            "opus",
        )
    if normalized == DEFAULT_MODEL_NAME:
        return LocalModelDefinition(
            DEFAULT_MODEL_NAME,
            MODEL_REPOSITORY,
            MODEL_REVISION,
            MODEL_LICENSE,
            MODEL_SIZE_BYTES,
            MODEL_MAX_DOWNLOAD_BYTES,
            MODEL_MAX_TOTAL_BYTES,
            MODEL_FILES,
            SMALL_MODEL_FILES,
            (),
            "madlad",
        )
    raise ValueError(f"Unsupported local translation model: {model_name}")


class LocalTranslationModelManager:
    """Manage one of the project's pinned offline CTranslate2 models."""

    def __init__(self, model_dir: Path | None = None, model_name: str | None = None) -> None:
        configured_name = os.getenv("LOCAL_TRANSLATION_MODEL", DEFAULT_MODEL_NAME)
        self.model_name = MODEL_ALIASES.get(
            (model_name or configured_name).strip().lower(), (model_name or configured_name).strip().lower()
        )
        self.definition = _definition(self.model_name)
        configured = os.getenv("LOCAL_TRANSLATION_MODEL_DIR", "").strip()
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        elif configured:
            self.model_dir = Path(configured)
        else:
            self.model_dir = BASE_DIR / "tools" / "models" / "translation" / self.model_name

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
        required = (*self.definition.model_files, *self.definition.small_model_files)
        missing = [name for name in required if not (self.model_dir / name).is_file()]
        if missing:
            return self._unavailable(f"missing files: {', '.join(missing)}")
        if self.model_dir.is_symlink():
            return self._unavailable("managed model directory is a symlink")
        total_size = 0
        for name, (expected_hash, expected_size) in self.definition.model_files.items():
            path = self.model_dir / name
            if path.is_symlink():
                return self._unavailable(f"symlinked model file: {name}")
            size = path.stat().st_size
            total_size += size
            if size != expected_size:
                return self._unavailable(f"size mismatch: {name}")
            if _sha256(path) != expected_hash:
                return self._unavailable(f"SHA-256 mismatch: {name}")
        for name, (max_size, required_keys) in self.definition.small_model_files.items():
            path = self.model_dir / name
            total_size += path.stat().st_size
            reason = _validate_small_model_file(path, max_size, required_keys)
            if reason:
                return self._unavailable(f"invalid metadata: {name}: {reason}")
        if total_size > self.definition.max_total_bytes:
            return self._unavailable(
                f"model exceeds {self.definition.max_total_bytes} byte installation budget: {total_size} bytes"
            )
        return LocalModelStatus(
            True,
            self.model_dir,
            self.definition.repository,
            self.definition.revision,
            self.definition.expected_size_bytes,
            self.definition.license,
            self.definition.name,
        )

    def _unavailable(self, reason: str) -> LocalModelStatus:
        return LocalModelStatus(
            False,
            self.model_dir,
            self.definition.repository,
            self.definition.revision,
            self.definition.expected_size_bytes,
            self.definition.license,
            self.definition.name,
            reason,
        )

    def ensure(self, *, confirm: Callable[[LocalModelStatus], bool] | None = None) -> Path:
        status = self.status()
        if status.available:
            return status.path
        if confirm is None or not confirm(status):
            workspace_bytes = (
                MODEL_DOWNLOAD_WORKSPACE_BYTES
                if self.definition.tokenizer_kind == "madlad"
                else self.definition.expected_size_bytes * 2
            )
            raise RuntimeError(
                f"Local translation model is not ready ({status.reason}). "
                f"Resource: {status.repository}@{status.revision}; "
                f"model size: {status.expected_size_bytes / 1_000_000:.0f} MB; "
                f"temporary download workspace: about {workspace_bytes / 1024**2:.0f} MiB; "
                f"destination: {self.model_dir}; license: {status.license}. "
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
            for name in (*self.definition.model_files, *self.definition.small_model_files):
                destination = download_dir / name
                if name in self.definition.bundled_model_files:
                    _write_bundled_model_file(name, destination)
                    continue
                url = (
                    f"https://huggingface.co/{self.definition.repository}/resolve/"
                    f"{self.definition.revision}/{name}?download=true"
                )
                limit = (
                    self.definition.model_files[name][1]
                    if name in self.definition.model_files
                    else self.definition.small_model_files[name][0]
                )
                _download_file(url, destination, min(self.definition.max_download_bytes, limit), self.huggingface_token)
            for name, (expected_hash, expected_size) in self.definition.model_files.items():
                path = download_dir / name
                if path.stat().st_size != expected_size or _sha256(path) != expected_hash:
                    raise RuntimeError(f"Integrity validation failed for downloaded model file: {name}")
            for name, (max_size, required_keys) in self.definition.small_model_files.items():
                reason = _validate_small_model_file(download_dir / name, max_size, required_keys)
                if reason:
                    raise RuntimeError(f"Integrity validation failed for downloaded metadata: {name}: {reason}")
            total_size = sum(
                (download_dir / name).stat().st_size
                for name in (*self.definition.model_files, *self.definition.small_model_files)
            )
            if total_size > self.definition.max_total_bytes:
                raise RuntimeError(
                    f"Downloaded model exceeds {self.definition.max_total_bytes} byte installation budget: {total_size} bytes"
                )
            metadata = {
                "model": self.definition.name,
                "repository": self.definition.repository,
                "revision": self.definition.revision,
                "license": self.definition.license,
                "expected_size_bytes": self.definition.expected_size_bytes,
                "files": {
                    name: {"sha256": expected_hash, "size": expected_size}
                    for name, (expected_hash, expected_size) in self.definition.model_files.items()
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
    """Offline Spanish→English translation using either pinned local model."""

    source_lang = "es"
    target_lang = "en"

    def __init__(
        self,
        settings,
        model_manager: LocalTranslationModelManager | None = None,
        model_name: str | None = None,
    ) -> None:
        selected_name = model_name or getattr(
            settings, "local_translation_model", os.getenv("LOCAL_TRANSLATION_MODEL", DEFAULT_MODEL_NAME)
        )
        self.settings = settings
        model_dir = getattr(settings, "local_translation_model_dir", None) if model_name is None else None
        self.manager = model_manager or LocalTranslationModelManager(model_dir, selected_name)
        self.definition = self.manager.definition
        configured_id = str(
            getattr(
                settings,
                "local_translation_model_id",
                os.getenv("LOCAL_TRANSLATION_MODEL_ID", self.definition.repository),
            )
        )
        configured_revision = str(
            getattr(
                settings,
                "local_translation_model_revision",
                os.getenv("LOCAL_TRANSLATION_MODEL_REVISION", self.definition.revision),
            )
        )
        if configured_id != self.definition.repository or configured_revision != self.definition.revision:
            raise ValueError("The local translation provider only accepts the pinned model repository and revision")
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
        if self.definition.tokenizer_kind == "opus":
            self._source = spm.SentencePieceProcessor(model_file=str(self.model_path / "source.spm"))
            self._target = spm.SentencePieceProcessor(model_file=str(self.model_path / "target.spm"))
        else:
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
        requested_device = (
            str(getattr(self.settings, "local_translation_device", os.getenv("LOCAL_TRANSLATION_DEVICE", "auto")))
            .lower()
            .strip()
        )
        requested_compute = (
            str(
                getattr(
                    self.settings, "local_translation_compute_type", os.getenv("LOCAL_TRANSLATION_COMPUTE_TYPE", "auto")
                )
            )
            .lower()
            .strip()
        )
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
        beam_size = max(
            1,
            int(getattr(self.settings, "local_translation_beam_size", os.getenv("LOCAL_TRANSLATION_BEAM_SIZE", 2))),
        )
        if self.definition.tokenizer_kind == "opus":
            tokens = [self._source.encode(text, out_type=str) + ["</s>"] for text in texts]
            results = self._translator.translate_batch(tokens, beam_size=beam_size)
        else:
            target_prefix = f"<2{self.target_lang}>"
            tokens = [self._tokenizer.encode(f"{target_prefix} {text}", out_type=str) for text in texts]
            results = self._translator.translate_batch(
                tokens,
                batch_type="tokens",
                beam_size=beam_size,
                no_repeat_ngram_size=1,
            )
        outputs: list[str] = []
        for result in results:
            hypotheses = getattr(result, "hypotheses", None) or []
            if not hypotheses:
                outputs.append("")
                continue
            tokens_out = list(hypotheses[0])
            if self.definition.tokenizer_kind == "opus":
                if "</s>" in tokens_out:
                    tokens_out = tokens_out[: tokens_out.index("</s>")]
                outputs.append(self._target.decode(tokens_out).strip())
            else:
                outputs.append(self._tokenizer.decode(tokens_out).strip())
        if len(outputs) != len(texts):
            raise RuntimeError(f"Local translation returned {len(outputs)} results for {len(texts)} inputs")
        return outputs


def _write_bundled_model_file(name: str, destination: Path) -> None:
    try:
        source = __import__("importlib").resources.files("config.local_translation_model").joinpath(name)
        content = source.read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise RuntimeError(f"Bundled local translation metadata is unavailable: {name}") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


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
    if parsed.scheme != "https" or parsed.netloc != "huggingface.co":
        raise ValueError("Model downloads are restricted to the pinned Hugging Face origin")
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "resolve":
        raise ValueError("Model download path is not a valid pinned repository file")
    repository = f"{parts[0]}/{parts[1]}"
    revision = parts[3]
    filename = "/".join(parts[4:])
    definition = None
    for candidate in MODEL_ALIASES.values():
        try:
            candidate_definition = _definition(candidate)
        except ValueError:
            continue
        if candidate_definition.repository == repository and candidate_definition.revision == revision:
            definition = candidate_definition
            break
    if definition is None or not filename or "/" in filename:
        raise ValueError("Model download path is not pinned to one of the supported model revisions")
    cache_dir = Path(tempfile.mkdtemp(prefix="video-translation-hf-cache-"))
    try:
        try:
            from huggingface_hub import hf_hub_download

            cached = Path(
                hf_hub_download(
                    repo_id=repository,
                    filename=filename,
                    revision=revision,
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
