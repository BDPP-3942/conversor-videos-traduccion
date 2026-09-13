import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

from src import local_translation
from src.local_translation import LocalTranslationModelManager, LocalTranslationProvider


def _madlad_test_files(monkeypatch):
    files = {
        "model.bin": (hashlib.sha256(b"model").hexdigest(), 5),
        "sentencepiece.model": (hashlib.sha256(b"sentencepiece").hexdigest(), 13),
    }
    metadata = {
        "config.json": (1024, ("decoder_start_token", "eos_token")),
        "shared_vocabulary.json": (4096, ()),
    }
    monkeypatch.setattr(local_translation, "MODEL_FILES", files)
    monkeypatch.setattr(local_translation, "SMALL_MODEL_FILES", metadata)
    monkeypatch.setattr(local_translation, "REQUIRED_FILES", (*files, *metadata))
    monkeypatch.setattr(local_translation, "MODEL_SIZE_BYTES", 18)
    monkeypatch.setattr(local_translation, "MODEL_MAX_TOTAL_BYTES", 4096)
    return files


def _opus_test_files(monkeypatch):
    files = {
        "model.bin": (hashlib.sha256(b"model").hexdigest(), 5),
        "source.spm": (hashlib.sha256(b"source").hexdigest(), 6),
        "target.spm": (hashlib.sha256(b"target").hexdigest(), 6),
    }
    metadata = {
        "config.json": (1024, ("decoder_start_token", "eos_token")),
        "shared_vocabulary.json": (4096, ()),
        "tokenizer_config.json": (1024, ("source_lang", "target_lang")),
    }
    monkeypatch.setattr(local_translation, "OPUS_MODEL_FILES", files)
    monkeypatch.setattr(local_translation, "OPUS_SMALL_MODEL_FILES", metadata)
    monkeypatch.setattr(local_translation, "OPUS_MODEL_SIZE_BYTES", 17)
    return files


def _write_madlad_model(path: Path, shared_vocabulary: str = "{}") -> None:
    path.joinpath("model.bin").write_bytes(b"model")
    path.joinpath("sentencepiece.model").write_bytes(b"sentencepiece")
    path.joinpath("config.json").write_text('{"decoder_start_token": "</s>", "eos_token": "</s>"}', encoding="utf-8")
    path.joinpath("shared_vocabulary.json").write_text(shared_vocabulary, encoding="utf-8")


def test_model_status_reports_missing_resource(tmp_path: Path) -> None:
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "missing files" in status.reason
    assert status.repository == local_translation.MODEL_REPOSITORY
    assert status.revision == local_translation.MODEL_REVISION


def test_model_status_accepts_verified_madlad_files(monkeypatch, tmp_path: Path) -> None:
    files = _madlad_test_files(monkeypatch)
    _write_madlad_model(tmp_path)
    status = LocalTranslationModelManager(tmp_path).status()
    assert status.available
    assert status.model_name == local_translation.DEFAULT_MODEL_NAME
    assert files["model.bin"][0] == hashlib.sha256(b"model").hexdigest()


def test_model_status_accepts_shared_vocabulary_array(monkeypatch, tmp_path: Path) -> None:
    _madlad_test_files(monkeypatch)
    _write_madlad_model(tmp_path, '["</s>", "<unk>", "hola"]')
    assert LocalTranslationModelManager(tmp_path).status().available


def test_opus_model_definition_is_preserved(monkeypatch, tmp_path: Path) -> None:
    files = _opus_test_files(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path, local_translation.OPUS_MODEL_NAME)
    tmp_path.joinpath("model.bin").write_bytes(b"model")
    tmp_path.joinpath("source.spm").write_bytes(b"source")
    tmp_path.joinpath("target.spm").write_bytes(b"target")
    tmp_path.joinpath("config.json").write_text('{"decoder_start_token":"</s>","eos_token":"</s>"}', encoding="utf-8")
    tmp_path.joinpath("shared_vocabulary.json").write_text('["</s>"]', encoding="utf-8")
    tmp_path.joinpath("tokenizer_config.json").write_text('{"source_lang":"spa","target_lang":"eng"}', encoding="utf-8")
    status = manager.status()
    assert status.available
    assert status.model_name == local_translation.OPUS_MODEL_NAME
    assert files["source.spm"][1] == 6


def test_model_status_rejects_wrong_hash(monkeypatch, tmp_path: Path) -> None:
    _madlad_test_files(monkeypatch)
    _write_madlad_model(tmp_path)
    tmp_path.joinpath("model.bin").write_bytes(b"wrong")
    status = LocalTranslationModelManager(tmp_path).status()
    assert not status.available
    assert "SHA-256 mismatch" in status.reason


def test_model_status_rejects_oversized_install(monkeypatch, tmp_path: Path) -> None:
    _madlad_test_files(monkeypatch)
    _write_madlad_model(tmp_path)
    monkeypatch.setattr(local_translation, "MODEL_MAX_TOTAL_BYTES", 10)
    assert "installation budget" in LocalTranslationModelManager(tmp_path).status().reason


def test_model_ensure_does_not_download_without_explicit_confirmation(monkeypatch, tmp_path: Path) -> None:
    _madlad_test_files(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path)
    try:
        manager.ensure(confirm=lambda _status: False)
    except RuntimeError as exc:
        assert "Prepare it explicitly" in str(exc)
        assert "temporary download workspace" in str(exc)
    else:
        raise AssertionError("missing local model must not be downloaded without confirmation")


def test_model_download_uses_pinned_huggingface_resource(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "model.bin"
    cached = tmp_path / "cached.bin"
    cached.write_bytes(b"abc")
    captured = {}

    def fake_download(**kwargs):
        captured.update(kwargs)
        return str(cached)

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=fake_download))
    local_translation._download_file(
        f"https://huggingface.co/{local_translation.MODEL_REPOSITORY}/resolve/{local_translation.MODEL_REVISION}/model.bin?download=true",
        destination,
        10,
    )
    assert captured["repo_id"] == local_translation.MODEL_REPOSITORY
    assert captured["revision"] == local_translation.MODEL_REVISION
    assert captured["token"] is None
    assert destination.read_bytes() == b"abc"


def test_local_translation_uses_madlad_target_prefix(monkeypatch, tmp_path: Path) -> None:
    _madlad_test_files(monkeypatch)
    _write_madlad_model(tmp_path)
    manager = LocalTranslationModelManager(tmp_path)

    class FakeSentencePiece:
        def __init__(self, model_file):
            assert Path(model_file).name == "sentencepiece.model"

        def encode(self, text, out_type=str):
            assert text.startswith("<2en> ")
            return ["▁hola", "▁mundo"]

        def decode(self, tokens):
            return "hello world" if tokens == ["hello", "world", "</s>"] else ""

    class FakeResult:
        hypotheses = [["hello", "world", "</s>"]]

    class FakeTranslator:
        def __init__(self, model_path, **kwargs):
            assert model_path == str(tmp_path)
            assert kwargs == {"device": "cpu", "compute_type": "int8"}

        def translate_batch(self, tokens, **kwargs):
            assert tokens == [["▁hola", "▁mundo"]]
            assert kwargs == {"batch_type": "tokens", "beam_size": 2, "no_repeat_ngram_size": 1}
            return [FakeResult()]

    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(Translator=FakeTranslator))
    monkeypatch.setitem(sys.modules, "sentencepiece", SimpleNamespace(SentencePieceProcessor=FakeSentencePiece))
    monkeypatch.setattr(
        local_translation,
        "detect_hardware",
        lambda: SimpleNamespace(gpu=SimpleNamespace(usable_for_whisper=False, device_index=0)),
    )
    settings = SimpleNamespace(
        local_translation_device="cpu", local_translation_compute_type="int8", local_translation_beam_size=2
    )
    provider = LocalTranslationProvider(settings, manager)
    assert provider.translate("Hola mundo") == "hello world"


def test_local_translation_cuda_probe_falls_back_to_cpu(monkeypatch) -> None:
    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider.settings = SimpleNamespace(
        local_translation_device="cuda", local_translation_compute_type="auto", detected_gpu_index=0
    )
    monkeypatch.setattr(
        local_translation,
        "detect_hardware",
        lambda: SimpleNamespace(gpu=SimpleNamespace(usable_for_whisper=True, device_index=0)),
    )

    class FakeCT2:
        @staticmethod
        def get_supported_compute_types(*_args):
            raise RuntimeError("CUDA unavailable")

    monkeypatch.setitem(sys.modules, "ctranslate2", FakeCT2)
    assert provider._resolve_runtime() == ("cpu", "int8", 0)
