import hashlib
import os
import sys
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


def test_model_download_uses_huggingface_hub_without_auth(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "model.bin"
    cached = tmp_path / "cached.bin"
    cached.write_bytes(b"abc")
    captured = {}

    def fake_download(**kwargs):
        captured.update(kwargs)
        return str(cached)

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=fake_download))
    local_translation._download_file(
        "https://huggingface.co/Prukario/opus-mt-es-en-ct2-int8/resolve/ad91ad1697ea1761111ff4c179400796d085b347/model.bin?download=true",
        destination,
        10,
    )

    assert captured["repo_id"] == local_translation.MODEL_REPOSITORY
    assert captured["revision"] == local_translation.MODEL_REVISION
    assert captured["token"] is None
    assert destination.read_bytes() == b"abc"


def test_model_download_uses_optional_huggingface_token(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "model.bin"
    cached = tmp_path / "cached.bin"
    cached.write_bytes(b"abc")
    captured = {}
    monkeypatch.setenv("TEST_HF_TOKEN", "hf_test_token")
    auth_token = os.environ["TEST_HF_TOKEN"]

    def fake_download(**kwargs):
        captured.update(kwargs)
        return str(cached)

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=fake_download))
    local_translation._download_file(
        "https://huggingface.co/Prukario/opus-mt-es-en-ct2-int8/resolve/ad91ad1697ea1761111ff4c179400796d085b347/model.bin?download=true",
        destination,
        10,
        auth_token=auth_token,
    )

    assert captured["token"] == auth_token
    assert destination.read_bytes() == b"abc"


def test_local_translation_batch_decodes_model_output() -> None:
    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider.settings = SimpleNamespace(local_translation_beam_size=2)

    class FakeSentencePiece:
        def encode(self, text, out_type=str):
            return ["▁hola", "▁mundo"] if text else []

        def decode(self, tokens):
            return "hello world" if tokens == ["hello", "world"] else ""

    class FakeResult:
        hypotheses = [["hello", "world", "</s>"]]

    class FakeTranslator:
        def translate_batch(self, tokens, beam_size):
            assert tokens == [["▁hola", "▁mundo", "</s>"], ["▁hola", "▁mundo", "</s>"]]
            assert beam_size == 2
            return [FakeResult(), FakeResult()]

    provider._source = FakeSentencePiece()
    provider._target = FakeSentencePiece()
    provider._translator = FakeTranslator()

    assert provider.translate_batch(["Hola mundo", "Hola mundo"]) == ["hello world", "hello world"]


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

    monkeypatch.setitem(sys.modules, "ctranslate2", FakeCT2)
    assert provider._resolve_runtime() == ("cpu", "int8", 0)
