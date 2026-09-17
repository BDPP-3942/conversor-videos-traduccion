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

    assert paths["input"].is_dir()
    assert paths["output"].is_dir()
    for key in ("work", "failures", "archive", "archive_sources", "logs", "state", "manifests"):
        assert not paths[key].exists(), key


def test_resolve_project_path_redirects_writable_frozen_paths(monkeypatch, tmp_path):
    import config.settings as settings

    monkeypatch.setattr(settings.sys, "frozen", True, raising=False)
    monkeypatch.setattr(settings, "USER_DATA_DIR", tmp_path / "user-data")
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path / "install")

    assert settings.resolve_project_path("storage/state/run.lock") == (
        tmp_path / "user-data" / "storage/state/run.lock"
    )
    assert settings.resolve_project_path("secrets/providers/default/token.json") == (
        tmp_path / "user-data" / "secrets/providers/default/token.json"
    )
    assert settings.resolve_project_path("tools/models/translation/model") == (
        tmp_path / "user-data" / "tools/models/translation/model"
    )
    assert settings.resolve_project_path("config/app.toml") == tmp_path / "install/config/app.toml"
