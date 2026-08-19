from pathlib import Path


def test_repository_storage_layout_is_canonical():
    storage = Path("storage")
    expected_gitkeep_dirs = [
        storage / "input",
        storage / "work",
        storage / "output" / "_manifests",
        storage / "archive" / "sources",
        storage / "state",
        storage / "failures",
        storage / "logs",
    ]

    for directory in expected_gitkeep_dirs:
        assert (directory / ".gitkeep").is_file()

    assert not (storage / "original_transcriptions").exists()


def test_gitignore_uses_general_storage_rules():
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "storage/*" in text
    assert "!storage/**/" in text
    assert "storage/**/*" in text
    assert "!storage/**/.gitkeep" in text
    assert "storage/input/*" not in text
    assert "storage/output/*" not in text
    assert "storage/archive/sources/*" not in text


def test_local_storage_paths_include_canonical_subfolders():
    from config.settings import local_storage_paths

    paths = local_storage_paths()
    assert paths["manifests"].as_posix().endswith("storage/output/_manifests")
    assert paths["archive_sources"].as_posix().endswith("storage/archive/sources")
