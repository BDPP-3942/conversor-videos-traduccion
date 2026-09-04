from pathlib import Path

from src.file_naming import (
    FileNameFormatter,
    fit_output_stem,
    normalize_comparison_key,
    normalize_component,
    normalize_filename,
)


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
    assert metadata.output_stem == "3_tai_chix07_forma_del_tigre"


def test_trailing_iso_hh_mm_timestamp_is_removed(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    source = root / "Curso 03 Tai Chi" / "07 Forma del Tigre_2026-08-31_10_24.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert "2026" not in metadata.output_stem
    assert "10_24" not in metadata.output_stem
    assert metadata.lesson == 7


def test_calendar_date_time_formats_are_removed_from_normalized_name() -> None:
    cases = (
        "Forma_31-08-2026_10:24:59.mp4",
        "Forma_31/08/2026_10:24:59.mp4",
        "Forma_08/31/2026_10:24:59.mp4",
        "Forma_2026-08-31_10:24:59.mp4",
        "Forma_2026/08/31 10:24:59.mp4",
        "Forma_2026.08.31T10.24.59.mp4",
        "Forma_20260831_102459.mp4",
        "Forma_31082026_102459.mp4",
        "Forma_08312026_102459.mp4",
    )
    for filename in cases:
        normalized = normalize_filename(filename)
        assert "2026" not in normalized
        assert "31_08_2026" not in normalized
        assert "08_31_2026" not in normalized
        assert "10_24_59" not in normalized


def test_calendar_date_time_suffix_is_removed_from_source_output(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    for timestamp in (
        "31-08-2026 10:24:59",
        "31/08/2026 10:24:59",
        "08/31/2026 10:24:59",
        "2026-08-31 10:24:59",
        "2026/08/31_10_24_59",
        "20260831_102459",
    ):
        source = root / "Curso 03 Tai Chi" / f"07 Forma del Tigre_{timestamp}.mp4"
        metadata = FileNameFormatter.resolve_source_metadata(source, root)
        assert metadata.lesson == 7
        assert "2026" not in metadata.output_stem
        assert "10_24" not in metadata.output_stem


def test_generated_output_stem_is_sanitized_to_lowercase_without_diacritics(tmp_path: Path) -> None:
    result = fit_output_stem("Curso-03: Niño / CON?", tmp_path)
    assert result == "curso_03_nino_con"
    assert "-" not in result
    assert "/" not in result
    assert ":" not in result
    assert "?" not in result


def test_generated_output_stem_normalizes_diacritics_and_case() -> None:
    decomposed = "Cafe\u0301xNin\u0303o"
    assert normalize_component(decomposed) == "cafexnino"


def test_generated_output_stem_handles_reserved_name_after_normalization(tmp_path: Path) -> None:
    assert normalize_component("CON") == "_con"
    assert fit_output_stem("CON", tmp_path) == "_con"


def test_generated_output_stem_keeps_scope_separator_and_sanitizes_each_block(tmp_path: Path) -> None:
    result = fit_output_stem("19x2-POSTURAS (FIJAS)", tmp_path)
    assert result == "19x2_posturas_fijas"
    assert result.count("x") == 1
    assert "-" not in result


def test_normalize_component_is_idempotent_and_removes_emoji() -> None:
    value = "CaféxNiño_äöüß_é🇪🇸"
    normalized = normalize_component(value)
    assert normalize_component(normalized) == normalized
    assert normalized == "cafexnino_aouss_e"


def test_normalize_filename_is_idempotent() -> None:
    value = "Leccio\u0301n_niño_2026-08-31.mp4"
    normalized = normalize_filename(value)
    assert normalize_filename(normalized) == normalized
    assert normalized == "leccion_nino.mp4"


def test_unicode_letters_are_preserved_but_diacritics_and_emoji_are_removed() -> None:
    value = "áéíóúñ äöüß é français 日本語 中文 한국어 😀"
    normalized = normalize_component(value)
    assert normalized == "aeioun_aouss_e_francais_日本語_中文_한국어"
    assert normalize_component(normalized) == normalized


def test_mojibake_is_not_silently_repaired() -> None:
    value = "CafÃ©_niÃ±o.mp4"
    assert normalize_filename(value) == "cafa_niamo.mp4"
