from pathlib import Path

from src.file_naming import FileNameFormatter, normalize_comparison_key


def test_course_number_and_description_are_preserved(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "Curso 12 movilidad articular" / "Leccion 3 rotacion de hombros.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course == 12
    assert metadata.course_name == "movilidad_articular"
    assert metadata.lesson == 3
    assert metadata.lesson_name == "rotacion_de_hombros"
    assert metadata.output_stem == "12_movilidad_articularx03_rotacion_de_hombros"


def test_course_description_is_preserved_without_course_number(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "Curso movilidad articular" / "2 - rotacion de hombros.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course is None
    assert metadata.course_name == "movilidad_articular"
    assert metadata.lesson == 2
    assert metadata.lesson_name == "rotacion_de_hombros"
    assert metadata.output_stem == "movilidad_articularx02_rotacion_de_hombros"


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


def test_trailing_compact_hh_mm_timestamp_is_removed(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "Curso 03 Tai Chi" / "07 Forma del Tigre_20260831_10_24.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.output_stem == "3_Tai_Chi x07_Forma_del_Tigre".replace(" ", "")


def test_trailing_iso_hh_mm_timestamp_is_removed(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "Curso 03 Tai Chi" / "07 Forma del Tigre_2026-08-31_10_24.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert "2026" not in metadata.output_stem
    assert "10_24" not in metadata.output_stem
    assert metadata.lesson == 7
