from pathlib import Path
from zipfile import ZipFile

import pytest

from src.extractor import ZipExtractor


def make_zip(path: Path, name: str, data: bytes = b"data") -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(name, data)


def make_cp437_zip(path: Path, name: str, data: bytes = b"data") -> None:
    """Create a ZIP whose member name is encoded with the ZIP legacy CP437 rule."""
    placeholder = "niZo.wmv"
    assert len(name) == len(placeholder)
    with ZipFile(path, "w") as archive:
        archive.writestr(placeholder, data)
    raw = path.read_bytes()
    encoded_placeholder = placeholder.encode("ascii")
    encoded_name = name.encode("cp437")
    assert len(encoded_placeholder) == len(encoded_name)
    path.write_bytes(raw.replace(encoded_placeholder, encoded_name))


def extractor(**overrides):
    values = dict(max_depth=3, max_files=10_000, max_total_size=10_000_000)
    values.update(overrides)
    return ZipExtractor(**values)


def test_zip_slip_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    make_zip(archive_path, "../../escape.txt")
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_absolute_windows_zip_path_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe-windows.zip"
    make_zip(archive_path, r"C:\escape.txt")
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_unc_windows_zip_path_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe-unc.zip"
    make_zip(archive_path, r"\\server\share\escape.txt")
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_windows_reserved_zip_component_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "reserved.zip"
    make_zip(archive_path, "folder/CON.txt")
    with pytest.raises(ValueError, match="Reserved Windows"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_global_extraction_limits_are_enforced(tmp_path: Path) -> None:
    archive_path = tmp_path / "large.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("a.txt", b"12345")
        archive.writestr("b.txt", b"67890")
    with pytest.raises(ValueError, match="Maximum extracted ZIP size"):
        extractor(max_total_size=9).extract_zip(archive_path, tmp_path / "out")


def test_supported_media_extensions_are_collected(tmp_path: Path) -> None:
    archive_path = tmp_path / "media.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("a.WMV", b"fake")
        archive.writestr("b.mkv", b"fake")
        archive.writestr("c.txt", b"ignore")
    result = extractor().extract_zip(archive_path, tmp_path / "out")
    assert sorted(path.name for path in result.media) == ["a.WMV", "b.mkv"]


def test_nested_zip_preserves_source_tree(tmp_path: Path) -> None:
    inner = tmp_path / "inner.zip"
    with ZipFile(inner, "w") as archive:
        archive.writestr("lesson.wmv", b"fake")
    outer = tmp_path / "outer.zip"
    with ZipFile(outer, "w") as archive:
        archive.write(inner, arcname="inner.zip")
    result = extractor().extract_zip(outer, tmp_path / "out")
    assert len(result.media) == 1
    assert result.media[0].relative_to(tmp_path / "out").parts[-3:-1] == ("outer", "inner")


def test_zip_member_unicode_is_canonicalized_to_nfc(tmp_path: Path) -> None:
    archive_path = tmp_path / "unicode.zip"
    decomposed = "Cafe\u0301/Leccio\u0301n.wmv"
    make_zip(archive_path, decomposed)
    result = extractor().extract_zip(archive_path, tmp_path / "out")
    assert result.media[0].name == "Lección.wmv"
    assert result.media[0].relative_to(tmp_path / "out").parts[-2] == "Café"


def test_zip_container_name_is_canonicalized_to_nfc(tmp_path: Path) -> None:
    decomposed_zip_name = "Cafe\u0301.zip"
    archive_path = tmp_path / decomposed_zip_name
    make_zip(archive_path, "lesson.wmv")
    result = extractor().extract_zip(archive_path, tmp_path / "out")
    assert result.media[0].relative_to(tmp_path / "out").parts[0] == "Café"


def test_unicode_normalization_collision_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "collision.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("Café.txt", b"one")
        archive.writestr("Cafe\u0301.txt", b"two")
    with pytest.raises(ValueError, match="ZIP path collision"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_unicode_normalization_collision_is_rejected_case_insensitively(tmp_path: Path) -> None:
    archive_path = tmp_path / "collision-case.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("Café.txt", b"one")
        archive.writestr("cafe\u0301.TXT", b"two")
    with pytest.raises(ValueError, match="ZIP path collision"):
        extractor().extract_zip(archive_path, tmp_path / "out")


def test_zip_uses_cp437_for_legacy_non_utf8_member_names(tmp_path: Path) -> None:
    archive_path = tmp_path / "cp437.zip"
    make_cp437_zip(archive_path, "niño.wmv")
    result = extractor().extract_zip(archive_path, tmp_path / "out")
    assert result.media[0].name == "niño.wmv"
