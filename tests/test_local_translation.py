import hashlib
from pathlib import Path

from src import local_translation
from src.local_translation import LocalTranslationModelManager, LocalTranslationProvider


def _small_model_files(monkeypatch):
    files = {
        "model.bin": (hashlib.sha256(b"model").hexdigest(), 5),
        "source.spm": (hashlib.sha256(b"source").hexdigest(), 6),
        "target.spm": (hashlib.sha256(b"target").hexdigest(), 6),
    }
    monkeypatch.setattr(local_translation, "MODEL_FILES", files)
    monkeypatch.setattr(local_translation, "SMALL_MODEL_FILES", ("config.json", "shared_vocabulary.json", "tokenizer_config.json"))
    monkeypatch.setattr(local_translation, "MODEL_SIZE_BYTES", 17)
    return files


def _write_small_metadata(path: Path) -> None:
    for name in local_translation.SMALL_MODEL_FILES:
        path.joinpath(name).write_text("{}", encoding="utf-8")


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


def test_model_ensure_does_not_download_without_explicit_confirmation(monkeypatch, tmp_path: Path) -> None:
    _small_model_files(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path)
    try:
        manager.ensure(confirm=lambda _status: False)
    except RuntimeError as exc:
        assert "Prepare it explicitly" in str(exc)
    else:
        raise AssertionError("missing local model must not be downloaded without confirmation")


def test_local_translation_runtime_falls_back_to_cpu_when_cuda_probe_fails(monkeypatch) -> None:
    class Settings:
        local_translation_device = "cuda"
        local_translation_compute_type = "auto"
        detected_gpu_usable = True
        detected_gpu_index = 0

    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider.settings = Settings()

    class FakeCT2:
        @staticmethod
        def get_supported_compute_types(*_args):
            raise RuntimeError("CUDA unavailable")

    monkeypatch.setitem(__import__("sys").modules, "ctranslate2", FakeCT2)
    assert provider._resolve_runtime() == ("cpu", "int8")
