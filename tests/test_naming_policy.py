from pathlib import Path

from src.naming_policy import resolve


def test_zip_number_becomes_course_and_video_number_becomes_lesson():
    metadata = resolve(Path("Curso_03/07_Forma_del_Tigre.mp4"), Path("."))
    assert metadata.course == 3
    assert metadata.lesson == 7
    assert metadata.output_stem == "3x07_Forma_del_Tigre"


def test_without_numbers_uses_container_text_as_code():
    metadata = resolve(
        Path("Taichi_Intermedio/Respiracion_y_movimiento.mp4"),
        Path("."),
    )
    assert metadata.course is None
    assert metadata.lesson is None
    assert metadata.course_name == "Taichi_Intermedio"
    assert metadata.output_stem == "Taichi_IntermedioxRespiracion_y_movimiento"


def test_without_container_uses_video_title_only():
    metadata = resolve(Path("Respiracion_y_movimiento.mp4"), Path("."))
    assert metadata.course is None
    assert metadata.lesson is None
    assert metadata.output_stem == "Respiracion_y_movimiento"


def test_download_noise_does_not_become_course_number():
    metadata = resolve(
        Path("wetransfer_20260826T120000Z_Curso_03/07_Forma_del_Tigre.mp4"),
        Path("."),
    )
    assert metadata.course == 3
    assert metadata.lesson == 7



def test_date_noise_formats_are_ignored_without_removing_course_or_lesson():
    for noisy_folder in (
        "download_2026-08-26_12-00-00_Curso_03",
        "download_26-08-2026_12-00-00_Curso_03",
        "download_2026.08.26T12:00:00_Curso_03",
        "download_20260826_120000_Curso_03",
    ):
        metadata = resolve(Path(noisy_folder) / "07_Forma_del_Tigre.mp4", Path("."))
        assert metadata.course == 3
        assert metadata.lesson == 7
        assert metadata.output_stem == "3x07_Forma_del_Tigre"


def test_textual_course_and_numeric_lesson_use_x_separator():
    metadata = resolve(Path("Taichi_Intermedio/02_Forma.mp4"), Path("."))
    assert metadata.course_name == "Taichi_Intermedio"
    assert metadata.lesson == 2
    assert metadata.output_stem == "Taichi_Intermediox02_Forma"


def test_numeric_course_and_textual_lesson_use_x_separator():
    metadata = resolve(Path("Curso_03/Forma_del_Tigre.mp4"), Path("."))
    assert metadata.course == 3
    assert metadata.lesson is None
    assert metadata.output_stem == "3xForma_del_Tigre"
