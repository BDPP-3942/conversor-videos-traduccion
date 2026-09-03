from pathlib import Path

from src.local_translation import (
    MODEL_FILES,
    MODEL_LICENSE,
    MODEL_REPOSITORY,
    MODEL_REVISION,
    LocalTranslationModelManager,
    LocalTranslationProvider,
)


def _write_valid_model_files(path: Path) -> None:
    for name, (_, size) in MODEL_FILES.items():
        path.joinpath(name).write_bytes(b"x" * size)


def test_model_status_reports_missing_resource(tmp_path: Path) -> None:
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "missing files" in status.reason
    assert status.repository == MODEL_REPOSITORY
    assert status.revision == MODEL_REVISION
    assert status.license == MODEL_LICENSE


def test_model_status_rejects_wrong_size_before_loading(tmp_path: Path) -> None:
    tmp_path.joinpath("model.bin").write_bytes(b"invalid")
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "missing files" in status.reason


def test_model_status_rejects_wrong_hash(tmp_path: Path) -> None:
    for name, (_, size) in MODEL_FILES.items():
        tmp_path.joinpath(name).write_bytes(b"x" * size)
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "SHA-256 mismatch" in status.reason


def test_model_ensure_does_not_download_without_explicit_confirmation(tmp_path: Path) -> None:
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
