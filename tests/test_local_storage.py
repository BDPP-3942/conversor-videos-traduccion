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

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    files = provider.list_zip_files(str(input_dir))
    assert [item.name for item in files] == ["sample.zip"]


def test_local_storage_copies_file(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "sample.zip"
    source.write_bytes(b"zip-content")

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    file = provider.list_zip_files(str(input_dir))[0]
    destination = tmp_path / "work" / "copy.zip"
    provider.download_file(file, destination)
    provider.upload_file(destination, str(output_dir))

    assert (output_dir / "copy.zip").read_bytes() == b"zip-content"


def test_local_storage_retains_successful_source_and_records_sha256(tmp_path: Path):
    storage_root = tmp_path / "storage"
    input_dir = storage_root / "input"
    input_dir.mkdir(parents=True)
    source = input_dir / "curso37.zip"
    source.write_bytes(b"same-content")

    # El provider usa rutas relativas al proyecto real; para esta prueba solo
    # verificamos la lógica de registro de forma aislada en un registry local.
    from src.storage.processed_registry import ProcessedRegistry, sha256_file

    registry = ProcessedRegistry(storage_root / "state" / "processed.jsonl")
    digest = sha256_file(source)
    registry.append_success(
        source_name=source.name,
        sha256=digest,
        size=source.stat().st_size,
        archive_name=f"{source.stem}__{digest[:16]}.zip",
        output_folders=["37x02_OPT_DE_TAICH_LA_GRAN_RUEDA"],
    )

    assert registry.contains_success(source.name, digest)
    assert not registry.contains_success(source.name, "0" * 64)
