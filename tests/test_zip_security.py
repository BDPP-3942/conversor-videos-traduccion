from pathlib import Path
from warnings import catch_warnings, simplefilter
from zipfile import ZipFile

import pytest

from src.extractor import ZipExtractor


def make_zip(path: Path, names: list[str]) -> None:
    with ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, b"data")


def extractor() -> ZipExtractor:
    return ZipExtractor(max_depth=3, max_files=100, max_total_size=1_000_000)


def test_windows_absolute_path_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "absolute.zip"
    make_zip(archive, ["C:/escape.txt"])
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive, tmp_path / "out")


def test_unc_path_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "unc.zip"
    make_zip(archive, ["//server/share/escape.txt"])
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive, tmp_path / "out")


def test_backslash_traversal_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "backslash.zip"
    make_zip(archive, [r"..\..\escape.txt"])
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive, tmp_path / "out")


def test_windows_reserved_component_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "reserved.zip"
    make_zip(archive, ["lessons/CON.txt"])
    with pytest.raises(ValueError, match="Reserved Windows ZIP path component"):
        extractor().extract_zip(archive, tmp_path / "out")


def test_case_and_unicode_normalization_collision_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "collision.zip"
    make_zip(archive, ["Café.txt", "Cafe\u0301.txt"])
    with pytest.raises(ValueError, match="ZIP path collision"):
        extractor().extract_zip(archive, tmp_path / "out")


def test_duplicate_logical_paths_are_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.zip"
    with catch_warnings():
        simplefilter("ignore", UserWarning)
        with ZipFile(archive, "w") as handle:
            handle.writestr("lesson.txt", b"first")
            handle.writestr("lesson.txt", b"second")
    with pytest.raises(ValueError, match="ZIP path collision"):
        extractor().extract_zip(archive, tmp_path / "dupout")
