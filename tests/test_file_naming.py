from pathlib import Path

from src.file_naming import FileNameFormatter


def test_course_and_lesson_are_inferred_from_tree() -> None:
    root = Path("/tmp/extracted")
    source = (
        root
        / "wetransfer_curso37_1o-optimizadores-de-taichi"
        / "2º opt de taich LA GRAN RUEDA.mp4"
    )
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course == 37
    assert metadata.lesson == 2
    assert metadata.output_stem == "37x02_opt_de_taich_LA_GRAN_RUEDA"
    assert metadata.review_required is False


def test_nested_download_without_numbers_uses_textual_code() -> None:
    root = Path("/tmp/extracted")
    source = (
        root
        / "drive-download-20260818T104028Z-1-002"
        / "wetransfer_directo-estudio-prof-sobre-la-danza-del-arco-iris-wmv"
        / "directo estudio prof sobre la danza del arco iris.wmv"
    )
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course is None
    assert metadata.lesson is None
    assert metadata.course_name == "directo_estudio_prof_sobre_la_danza_del_arco_iris"
    assert metadata.output_stem == (
        "directo_estudio_prof_sobre_la_danza_del_arco_iris_"
        "directo_estudio_prof_sobre_la_danza_del_arco_iris"
    )
    assert metadata.review_required is True


def test_names_are_normalized_for_wordpress_safe_names() -> None:
    normalized = FileNameFormatter.normalize_video_name(
        "Vídeo nº 2 — Introducción: ¿Qué es el área? ñ.mp4"
    )
    assert normalized == "Video_no_2_Introduccion_Que_es_el_area_n.mp4"


def test_unsafe_windows_characters_are_replaced() -> None:
    normalized = FileNameFormatter.normalize_video_name('a:b*d?.mp4')
    assert normalized == "a_b_d.mp4"


def test_output_stem_reserves_room_for_vtt_suffix(tmp_path: Path) -> None:
    from src.file_naming import fit_output_stem
    from src.path_limits import get_filesystem_limits

    limits = get_filesystem_limits(tmp_path)
    base = "a" * limits.max_component
    result = fit_output_stem(base, tmp_path, reserve_suffixes=("_en.vtt", "_original.vtt"))
    assert len((result + "_original.vtt").encode("utf-8")) <= limits.max_component


def test_text_course_name_becomes_textual_code() -> None:
    root = Path("/tmp/extracted")
    source = root / "Curso posturas estiramientos" / "Lección saludo al sol.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course is None
    assert metadata.course_name == "posturas_estiramientos"
    assert metadata.lesson is None
    assert metadata.output_stem == "posturas_estiramientos_saludo_al_sol"
    assert metadata.review_required is True


def test_compression_download_noise_is_ignored() -> None:
    root = Path("/tmp/extracted")
    source = (
        root
        / "drive-download-20260818T104028Z-1-002"
        / "Curso movilidad articular"
        / "2 - rotacion de hombros.mp4"
    )
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course_name == "movilidad_articular"
    assert metadata.lesson == 2
    assert "drive" not in metadata.output_stem.lower()
    assert metadata.output_stem.startswith("movilidad_articular_02_")


def test_arbitrary_text_becomes_textual_course_code() -> None:
    root = Path("/tmp/extracted")
    source = root / "wetransfer_material-estudio" / "saludo-inicial.mp4"
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.course is None
    assert metadata.course_name == "material_estudio"
    assert metadata.lesson is None
    assert metadata.output_stem == "material_estudio_saludo_inicial"
