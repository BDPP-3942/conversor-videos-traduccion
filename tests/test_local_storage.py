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