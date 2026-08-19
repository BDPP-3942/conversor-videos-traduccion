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


def test_nested_drive_download_source_is_ambiguous() -> None:
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
    assert metadata.output_stem.startswith("SIN_CURSOxSIN_LECCION_")
    assert metadata.review_required is True
