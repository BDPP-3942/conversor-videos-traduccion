from __future__ import annotations

import src.runtime_paths as runtime_paths


def test_runtime_paths_keep_media_in_documents_and_state_private(monkeypatch, tmp_path):
    documents = tmp_path / "Documents"
    monkeypatch.setattr(runtime_paths, "documents_root", lambda: documents)
    monkeypatch.setattr(
        runtime_paths,
        "user_data_root",
        lambda: tmp_path / "LocalAppData" / runtime_paths.APP_NAME,
    )

    paths = runtime_paths.runtime_storage_paths()

    assert paths["input"] == documents / "Video Translation Pipeline" / "input"
    assert paths["output"] == documents / "Video Translation Pipeline" / "output"
    assert paths["logs"].is_relative_to(tmp_path / "LocalAppData")
    assert paths["state"].is_relative_to(tmp_path / "LocalAppData")
    assert not paths["input"].is_relative_to(paths["root"])
    assert not paths["output"].is_relative_to(paths["root"])


def test_ensure_runtime_storage_creates_all_writable_directories(monkeypatch, tmp_path):
    documents = tmp_path / "Documents"
    state = tmp_path / "LocalAppData" / runtime_paths.APP_NAME
    monkeypatch.setattr(runtime_paths, "documents_root", lambda: documents)
    monkeypatch.setattr(runtime_paths, "user_data_root", lambda: state)

    paths = runtime_paths.ensure_runtime_storage()

    for key in (
        "input",
        "output",
        "work",
        "failures",
        "archive",
        "archive_sources",
        "logs",
        "state",
        "manifests",
    ):
        assert paths[key].is_dir(), key


def test_managed_relative_paths_resolve_to_private_user_data(monkeypatch, tmp_path):
    import config.settings as settings

    monkeypatch.setattr(settings, "BASE_DIR", tmp_path / "install")
    monkeypatch.setattr(settings, "user_data_root", lambda: tmp_path / "user-data")
    monkeypatch.setattr(settings, "STORAGE_DIR", tmp_path / "user-data")
    monkeypatch.setattr(settings, "SECRETS_DIR", tmp_path / "user-data" / "secrets")
    monkeypatch.setattr(settings, "MANAGED_TOOLS_DIR", tmp_path / "user-data" / "tools")

    assert settings.resolve_project_path("storage/output") == tmp_path / "user-data" / "storage/output"
    assert settings.resolve_project_path("secrets/providers") == tmp_path / "user-data" / "secrets/providers"
    assert settings.resolve_project_path("tools/models/translation") == tmp_path / "user-data" / "tools/models/translation"
    assert settings.resolve_project_path("config/app.toml") == tmp_path / "install/config/app.toml"
