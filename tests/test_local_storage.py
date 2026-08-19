from pathlib import Path
from zipfile import ZipFile

from src.storage.local import LocalStorageProvider


def test_local_storage_lists_nested_zips(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    nested = input_dir / "nested"
    nested.mkdir()
    with ZipFile(nested / "sample.zip", "w") as archive:
        archive.writestr("video.wmv", b"fake")

    provider = LocalStorageProvider(archive_successful=False, input_min_age_seconds=0)
    files = provider.list_zip_files(str(input_dir))
    assert [item.name for item in files] == ["sample.zip"]


def test_local_storage_copies_file(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "sample.zip"
    source.write_bytes(b"zip-content")

    provider = LocalStorageProvider(archive_successful=False, input_min_age_seconds=0)
    file = provider.list_zip_files(str(input_dir))[0]
    destination = tmp_path / "work" / "copy.zip"
    provider.download_file(file, destination)
    provider.upload_file(destination, str(output_dir))

    assert (output_dir / "copy.zip").read_bytes() == b"zip-content"
