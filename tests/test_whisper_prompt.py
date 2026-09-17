from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from src.stt_engine import STTEngine
from src.whisper_prompt import resolve_initial_prompt


def test_literal_prompt_remains_compatible(tmp_path: Path) -> None:
    prompt, source = resolve_initial_prompt("Tai Chi, taijiquan", tmp_path)
    assert prompt == "Tai Chi, taijiquan"
    assert source == "literal"


def test_txt_and_markdown_context_files(tmp_path: Path) -> None:
    for extension in (".txt", ".md"):
        path = tmp_path / f"palabras_contexto{extension}"
        path.write_text("Tai Chi\nqigong\n", encoding="utf-8")
        prompt, source = resolve_initial_prompt(path.name, tmp_path)
        assert prompt == "Tai Chi qigong"
        assert source == str(path.resolve())


def test_csv_context_joins_cells(tmp_path: Path) -> None:
    path = tmp_path / "palabras_contexto.csv"
    path.write_text("Tai Chi,qigong\nTaijiquan,\n", encoding="utf-8")
    prompt, source = resolve_initial_prompt(path.name, tmp_path)
    assert prompt == "Tai Chi, qigong, Taijiquan"
    assert source == str(path.resolve())


def test_docx_context_reads_paragraph_text_without_external_dependency(tmp_path: Path) -> None:
    path = tmp_path / "palabras_contexto.docx"
    document_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b"<w:body><w:p><w:r><w:t>Tai Chi</w:t></w:r></w:p>"
        b"<w:p><w:r><w:t>Taijiquan</w:t></w:r></w:p></w:body></w:document>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    prompt, source = resolve_initial_prompt(path.name, tmp_path)
    assert prompt == "Tai Chi Taijiquan"
    assert source == str(path.resolve())


def test_missing_context_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_initial_prompt("palabras_contexto.txt", tmp_path)


def test_empty_value_discovers_generic_context_file(tmp_path: Path) -> None:
    path = tmp_path / "palabras_contexto.txt"
    path.write_text("Tai Chi", encoding="utf-8")
    prompt, source = resolve_initial_prompt("", tmp_path)
    assert prompt == "Tai Chi"
    assert source == str(path.resolve())


def test_context_prompt_is_forwarded_to_whisper_transcription(monkeypatch, tmp_path: Path) -> None:
    context_path = tmp_path / "palabras_contexto.txt"
    context_path.write_text("Tai Chi taijiquan", encoding="utf-8")
    settings = SimpleNamespace(
        whisper_initial_prompt=str(context_path),
        whisper_vad_filter=False,
        whisper_min_silence_duration_ms=2000,
        source_lang="es",
        whisper_beam_size=5,
        whisper_compression_ratio_threshold=2.4,
        whisper_log_prob_threshold=-1.0,
        whisper_no_speech_threshold=0.6,
        whisper_hallucination_silence_threshold=None,
        whisper_condition_on_previous_text=True,
        whisper_recovery_retries=0,
        whisper_subtitle_split_silence_duration_ms=1000,
    )
    engine = object.__new__(STTEngine)
    engine.settings = settings
    engine.device = "cpu"
    engine.compute_type = "int8"
    engine._quality_thresholds = SimpleNamespace()

    captured: dict[str, object] = {}

    class FakeModel:
        def transcribe(self, media_path: str, **kwargs):
            captured.update(kwargs)
            return ([], SimpleNamespace())

    engine.model = FakeModel()
    monkeypatch.setattr(engine, "_is_suspicious", lambda segment: False)
    engine.transcribe(tmp_path / "audio.wav")

    assert captured["initial_prompt"] == "Tai Chi taijiquan"
