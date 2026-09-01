from pathlib import Path
from zipfile import ZipFile

import pytest

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
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>Tai Chi</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Taijiquan</w:t></w:r></w:p></w:body></w:document>'
    ).encode()
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
