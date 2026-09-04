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


def test_local_storage_zero_age_includes_file_created_immediately(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    source = input_dir / "sample.zip"
    source.write_bytes(b"zip-content")

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    files = provider.list_zip_files(str(input_dir))

    assert [item.name for item in files] == ["sample.zip"]


def test_local_storage_retains_successful_source_and_records_sha256(tmp_path: Path):
    storage_root = tmp_path / "storage"
    input_dir = storage_root / "input"
    input_dir.mkdir(parents=True)
    source = input_dir / "curso37.zip"
    source.write_bytes(b"same-content")

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


def test_finalize_source_is_idempotent_when_source_was_removed(tmp_path: Path, monkeypatch):
    provider = LocalStorageProvider(retain_sources=True, input_min_age_seconds=0)
    missing = tmp_path / "missing.zip"
    file = type("StorageFileLike", (), {"id": str(missing), "name": missing.name})()
    provider.finalize_source(file, "success", [])


def test_finalize_source_handles_race_during_fingerprint(tmp_path: Path, monkeypatch):
    provider = LocalStorageProvider(retain_sources=True, input_min_age_seconds=0)
    source = tmp_path / "race.zip"
    source.write_bytes(b"content")
    file = type("StorageFileLike", (), {"id": str(source), "name": source.name})()
    original = provider.source_fingerprint

    def disappear(_file):
        source.unlink(missing_ok=True)
        return original(_file)

    monkeypatch.setattr(provider, "source_fingerprint", disappear)
    provider.finalize_source(file, "success", [])


def test_local_output_name_migration_preserves_existing_unicode_names(tmp_path: Path):
    output = tmp_path / "output"
    legacy = output / "37x02_Téma_ñ"
    original = legacy / "original_transcriptions"
    original.mkdir(parents=True)
    (legacy / "37x02_Téma_ñ.mp4").write_bytes(b"video")
    (legacy / "37x02_Téma_ñ_en.vtt").write_text("WEBVTT\n", encoding="utf-8")
    (original / "37x02_Téma_ñ_original.vtt").write_text("WEBVTT\n", encoding="utf-8")

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    provider.normalize_existing_output_names(str(output), "original_transcriptions")

    canonical = output / "37x02_tema_n"
    canonical_original = canonical / "original_transcriptions"
    assert not legacy.exists()
    assert canonical.is_dir()
    assert (canonical / "37x02_tema_n.mp4").is_file()
    assert (canonical / "37x02_tema_n_en.vtt").is_file()
    assert (canonical_original / "37x02_tema_n_original.vtt").is_file()


def test_normalize_existing_outputs_fits_old_long_names(tmp_path: Path, monkeypatch):
    from config import settings as settings_module
    from src import path_limits
    from src.path_limits import FileSystemLimits

    monkeypatch.setattr(settings_module, "BASE_DIR", tmp_path)
    monkeypatch.setattr(settings_module, "STORAGE_DIR", tmp_path / "storage")
    monkeypatch.setattr(
        path_limits,
        "get_filesystem_limits",
        lambda _path: FileSystemLimits(max_component=40, max_path=260, platform="windows", source="test"),
    )
    root = tmp_path / "storage" / "output"
    root.mkdir(parents=True)
    long_name = "Video_" + ("a" * 70)
    folder = root / long_name
    folder.mkdir()
    (folder / f"{long_name}.mp4").write_bytes(b"video")
    (folder / f"{long_name}.mp3").write_bytes(b"audio")
    (folder / f"{long_name}_en.vtt").write_text("WEBVTT\n", encoding="utf-8")
    original = folder / "original_transcriptions"
    original.mkdir()
    (original / f"{long_name}_original.vtt").write_text("WEBVTT\n", encoding="utf-8")

    provider = LocalStorageProvider()
    mapping = provider.normalize_existing_output_names("storage/output", "original_transcriptions")

    assert mapping
    folders = [p for p in root.iterdir() if p.is_dir()]
    assert len(folders) == 1
    assert len(folders[0].name.encode("utf-8")) <= 40
    assert any(p.suffix == ".mp4" for p in folders[0].iterdir())


def test_local_storage_rename_output_folder_updates_artifact_stems(tmp_path: Path):
    output = tmp_path / "output"
    legacy = output / "Tema_viejo"
    original = legacy / "original_transcriptions"
    original.mkdir(parents=True)
    (legacy / "Tema_viejo.mp4").write_bytes(b"video")
    (legacy / "Tema_viejo.webm").write_bytes(b"webm")
    (legacy / "Tema_viejo_en.vtt").write_text("WEBVTT\n", encoding="utf-8")
    (original / "Tema_viejo_original.vtt").write_text("WEBVTT\n", encoding="utf-8")

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    mapping = provider.rename_output_folder(str(output), "Tema_viejo", "37x02_Tema_nuevo", "original_transcriptions")

    assert mapping == {"Tema_viejo": "37x02_Tema_nuevo"}
    assert (output / "37x02_Tema_nuevo" / "37x02_Tema_nuevo.mp4").is_file()
    assert (output / "37x02_Tema_nuevo" / "37x02_Tema_nuevo.webm").is_file()
    assert (output / "37x02_Tema_nuevo" / "37x02_Tema_nuevo_en.vtt").is_file()
    assert (output / "37x02_Tema_nuevo" / "original_transcriptions" / "37x02_Tema_nuevo_original.vtt").is_file()
