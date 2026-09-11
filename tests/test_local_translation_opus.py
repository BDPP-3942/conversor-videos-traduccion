import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

from src import local_translation
from src.local_translation import LocalTranslationModelManager, LocalTranslationProvider


def _patch_opus_artifacts(monkeypatch):
    model_files = {
        "model.bin": (hashlib.sha256(b"model").hexdigest(), 5),
        "source.spm": (hashlib.sha256(b"source").hexdigest(), 6),
        "target.spm": (hashlib.sha256(b"target").hexdigest(), 6),
    }
    metadata = {
        "config.json": (1024, ("decoder_start_token", "eos_token")),
        "shared_vocabulary.json": (4096, ()),
        "tokenizer_config.json": (1024, ("source_lang", "target_lang")),
    }
    monkeypatch.setattr(local_translation, "OPUS_MODEL_FILES", model_files)
    monkeypatch.setattr(local_translation, "OPUS_SMALL_MODEL_FILES", metadata)
    monkeypatch.setattr(local_translation, "OPUS_MODEL_SIZE_BYTES", 17)
    return model_files


def _write_opus_model(path: Path) -> None:
    path.joinpath("model.bin").write_bytes(b"model")
    path.joinpath("source.spm").write_bytes(b"source")
    path.joinpath("target.spm").write_bytes(b"target")
    path.joinpath("config.json").write_text('{"decoder_start_token":"</s>","eos_token":"</s>"}', encoding="utf-8")
    path.joinpath("shared_vocabulary.json").write_text('["</s>"]', encoding="utf-8")
    path.joinpath("tokenizer_config.json").write_text('{"source_lang":"spa","target_lang":"eng"}', encoding="utf-8")


def test_opus_status_requires_all_original_artifacts(monkeypatch, tmp_path: Path) -> None:
    _patch_opus_artifacts(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path, local_translation.OPUS_MODEL_NAME)
    _write_opus_model(tmp_path)
    status = manager.status()
    assert status.available
    assert status.model_name == local_translation.OPUS_MODEL_NAME
    assert status.repository == local_translation.OPUS_MODEL_REPOSITORY
    assert status.revision == local_translation.OPUS_MODEL_REVISION

    (tmp_path / "target.spm").unlink()
    status = manager.status()
    assert not status.available
    assert "target.spm" in status.reason


def test_opus_status_validates_hash_and_metadata(monkeypatch, tmp_path: Path) -> None:
    _patch_opus_artifacts(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path, local_translation.OPUS_MODEL_NAME)
    _write_opus_model(tmp_path)
    (tmp_path / "model.bin").write_bytes(b"wrong")
    status = manager.status()
    assert not status.available
    assert "SHA-256 mismatch: model.bin" in status.reason

    (tmp_path / "model.bin").write_bytes(b"model")
    (tmp_path / "tokenizer_config.json").write_text("not-json", encoding="utf-8")
    status = manager.status()
    assert not status.available
    assert "invalid metadata: tokenizer_config.json" in status.reason


def test_opus_provider_uses_source_and_target_sentencepiece(monkeypatch, tmp_path: Path) -> None:
    _patch_opus_artifacts(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path, local_translation.OPUS_MODEL_NAME)
    _write_opus_model(tmp_path)

    class FakeSentencePiece:
        def __init__(self, model_file):
            assert Path(model_file).name in {"source.spm", "target.spm"}

        def encode(self, text, out_type=str):
            assert text == "Hola mundo"
            return ["▁hola", "▁mundo"]

        def decode(self, tokens):
            return "hello world" if tokens == ["hello", "world"] else ""

    class FakeResult:
        hypotheses = [["hello", "world", "</s>"]]

    class FakeTranslator:
        def __init__(self, model_path, **kwargs):
            assert model_path == str(tmp_path)
            assert kwargs == {"device": "cpu", "compute_type": "int8"}

        def translate_batch(self, tokens, beam_size):
            assert tokens == [["▁hola", "▁mundo", "</s>"]]
            assert beam_size == 2
            return [FakeResult()]

    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(Translator=FakeTranslator))
    monkeypatch.setitem(sys.modules, "sentencepiece", SimpleNamespace(SentencePieceProcessor=FakeSentencePiece))
    monkeypatch.setattr(
        local_translation,
        "detect_hardware",
        lambda: SimpleNamespace(gpu=SimpleNamespace(usable_for_whisper=False, device_index=0)),
    )
    settings = SimpleNamespace(
        local_translation_device="cpu",
        local_translation_compute_type="int8",
        local_translation_beam_size=2,
        local_translation_model_id=local_translation.OPUS_MODEL_REPOSITORY,
        local_translation_model_revision=local_translation.OPUS_MODEL_REVISION,
    )
    provider = LocalTranslationProvider(settings, manager, local_translation.OPUS_MODEL_NAME)
    assert provider.translate("Hola mundo") == "hello world"


def test_opus_selection_rejects_mismatched_pinned_identity(monkeypatch, tmp_path: Path) -> None:
    _patch_opus_artifacts(monkeypatch)
    manager = LocalTranslationModelManager(tmp_path, local_translation.OPUS_MODEL_NAME)
    _write_opus_model(tmp_path)
    settings = SimpleNamespace(
        local_translation_device="cpu",
        local_translation_compute_type="int8",
        local_translation_beam_size=2,
        local_translation_model_id="cstr/madlad400-3b-ct2-int8",
        local_translation_model_revision=local_translation.OPUS_MODEL_REVISION,
    )
    try:
        LocalTranslationProvider(settings, manager, local_translation.OPUS_MODEL_NAME)
    except ValueError as exc:
        assert "pinned model repository" in str(exc)
    else:
        raise AssertionError("mismatched OPUS repository must be rejected")
