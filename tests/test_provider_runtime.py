from src.auth.rclone_manager import _asset_name
from src.providers.runtime import load_runtime, save_runtime


def test_runtime_provider_selection_roundtrip(tmp_path, monkeypatch):
    import src.providers.runtime as runtime

    target = tmp_path / "runtime.toml"
    monkeypatch.setattr(runtime, "RUNTIME_FILE", target)
    save_runtime(
        provider="rclone",
        profile="dropbox",
        source="rclone://input",
        target="rclone://output",
        rclone_remote="dropbox"
    )
    active = load_runtime()["active"]
    assert active["provider"] == "rclone"
    assert active["profile"] == "dropbox"
    assert active["rclone_remote"] == "dropbox"


def test_rclone_asset_name_is_deterministic(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr("platform.machine", lambda: "AMD64")
    assert _asset_name("1.75.0") == "rclone-v1.75.0-windows-amd64.zip"


def test_rclone_healthcheck_uses_read_only_listing(monkeypatch, tmp_path):
    from src.auth.rclone_manager import RcloneManager

    class FakeResult:
        returncode = 0
        stdout = "[]"
        stderr = ""

    manager = RcloneManager(tmp_path / "rclone", tmp_path / "rclone.conf")
    monkeypatch.setattr(manager, "ensure_binary", lambda: manager.binary_path)
    monkeypatch.setattr(manager, "_run", lambda args, check, timeout=300: FakeResult())
    result = manager.healthcheck("dropbox_main", "input")
    assert result["healthy"] is True
    assert result["remote"] == "dropbox_main"
    assert result["location"] == "input"
