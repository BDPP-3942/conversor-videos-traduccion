import hashlib
from pathlib import Path
from types import SimpleNamespace

from src import local_translation
from src.local_translation import LocalTranslationModelManager, LocalTranslationProvider


def _small_model_files(monkeypatch):
    files = {
        "model.bin": (hashlib.sha256(b"model").hexdigest(), 5),
        "source.spm": (hashlib.sha256(b"source").hexdigest(), 6),
        "target.spm": (hashlib.sha256(b"target").hexdigest(), 6),
    }
    monkeypatch.setattr(local_translation, "MODEL_FILES", files)
    monkeypatch.setattr(
        local_translation,
        "SMALL_MODEL_FILES",
        {
            "config.json": (1024, ("decoder_start_token", "eos_token")),
            "shared_vocabulary.json": (4096, ()),
            "tokenizer_config.json": (1024, ("source_lang", "target_lang")),
        },
    )
    monkeypatch.setattr(local_translation, "MODEL_SIZE_BYTES", 17)
    return files


def _write_small_metadata(path: Path) -> None:
    path.joinpath("config.json").write_text('{"decoder_start_token": "</s>", "eos_token": "</s>"}', encoding="utf-8")
    path.joinpath("shared_vocabulary.json").write_text("{}", encoding="utf-8")
    path.joinpath("tokenizer_config.json").write_text('{"source_lang": "spa", "target_lang": "eng"}', encoding="utf-8")


def test_model_status_reports_missing_resource(tmp_path: Path) -> None:
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "missing files" in status.reason
    assert status.repository == local_translation.MODEL_REPOSITORY
    assert status.revision == local_translation.MODEL_REVISION
    assert status.license == local_translation.MODEL_LICENSE


def test_model_status_accepts_verified_files(monkeypatch, tmp_path: Path) -> None:
    files = _small_model_files(monkeypatch)
    tmp_path.joinpath("model.bin").write_bytes(b"model")
    tmp_path.joinpath("source.spm").write_bytes(b"source")
    tmp_path.joinpath("target.spm").write_bytes(b"target")
    _write_small_metadata(tmp_path)
    status = LocalTranslationModelManager(tmp_path).status()
    assert status.available
    assert status.path == tmp_path
    assert files["model.bin"][0] == hashlib.sha256(b"model").hexdigest()


def test_model_status_rejects_wrong_hash(monkeypatch, tmp_path: Path) -> None:
    _small_model_files(monkeypatch)
    tmp_path.joinpath("model.bin").write_bytes(b"wrong")
    tmp_path.joinpath("source.spm").write_bytes(b"source")
    tmp_path.joinpath("target.spm").write_bytes(b"target")
    _write_small_metadata(tmp_path)
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "SHA-256 mismatch" in status.reason


def test_model_status_rejects_malformed_metadata(monkeypatch, tmp_path: Path) -> None:
    _small_model_files(monkeypatch)
    tmp_path.joinpath("model.bin").write_bytes(b"model")
    tmp_path.joinpath("source.spm").write_bytes(b"source")
    tmp_path.joinpath("target.spm").write_bytes(b"target")
    _write_small_metadata(tmp_path)
    tmp_path.joinpath("config.json").write_text("not-json", encoding="utf-8")
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "invalid metadata: config.json" in status.reason


def test_model_ensure_does_not_download_without_explicit_confirmation(monkeypatch, tmp_path: Path) -> None:
    _small_model_files(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path)
    try:
        manager.ensure(confirm=lambda _status: False)
    except RuntimeError as exc:
        assert "Prepare it explicitly" in str(exc)
    else:
        raise AssertionError("missing local model must not be downloaded without confirmation")


def test_model_download_resumes_partial_file(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "model.bin"
    partial = destination.with_suffix(".bin.part")
    partial.write_bytes(b"abc")

    class Response:
        status = 206
        headers = {"Content-Length": "3"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        @staticmethod
        def read(_size: int) -> bytes:
            if not hasattr(Response.read, "done"):
                Response.read.done = True
                return b"def"
            return b""

    monkeypatch.setattr(local_translation.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())
    local_translation._download_file("https://huggingface.co/pinned/model.bin", destination, 10)

    assert destination.read_bytes() == b"abcdef"
    assert not partial.exists()


def test_local_translation_runtime_falls_back_to_cpu_when_cuda_probe_fails(monkeypatch) -> None:
    settings = SimpleNamespace(
        local_translation_device="cuda",
        local_translation_compute_type="auto",
        detected_gpu_index=0,
    )
    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider.settings = settings
    monkeypatch.setattr(
        local_translation,
        "detect_hardware",
        lambda: SimpleNamespace(
            gpu=SimpleNamespace(
                usable_for_whisper=True,
                device_index=0,
                model="test-gpu",
                vram_free_gb=8.0,
                runtime="cuda",
            )
        ),
    )

    class FakeCT2:
        @staticmethod
        def get_supported_compute_types(*_args):
            raise RuntimeError("CUDA unavailable")

    monkeypatch.setitem(__import__("sys").modules, "ctranslate2", FakeCT2)
    assert provider._resolve_runtime() == ("cpu", "int8", 0)
