from pathlib import Path

from src.file_naming import FileNameFormatter, normalize_comparison_key


def test_compression_download_noise_is_ignored(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = (
        root / "drive-download-20260818T104028Z-1-002" / "Curso movilidad articular" / "2 - rotacion de hombros.mp4"
    )
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course_name == "movilidad_articular"
    assert metadata.lesson == 2
    assert "drive" not in metadata.output_stem.lower()
    assert metadata.output_stem.startswith("movilidad_articularx02_")


def test_arbitrary_text_becomes_textual_course_code(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "wetransfer_material-estudio" / "saludo-inicial.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course is None
    assert metadata.course_name == "material_estudio"
    assert metadata.lesson is None
    assert metadata.output_stem == "material_estudioxsaludo_inicial"


def test_normalize_comparison_key_removes_generic_tokens() -> None:
    assert normalize_comparison_key("video_03_forma_del_tigre.mp4") == "03 forma del tigre"
