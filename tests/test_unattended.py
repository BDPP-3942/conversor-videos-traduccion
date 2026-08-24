
from src.providers.runtime import load_runtime, save_runtime
from src.runtime_lock import RunLock


def test_runtime_keeps_active_cloud_locations(tmp_path, monkeypatch):
    import src.providers.runtime as runtime
    monkeypatch.setattr(runtime, "RUNTIME_FILE", tmp_path / "runtime.toml")
    save_runtime(
        provider="google_drive",
        profile="company",
        source="gdrive://source123",
        target="gdrive://target456",
        archive="archive789",
    )
    active = load_runtime()["active"]
    assert active["provider"] == "google_drive"
    assert active["profile"] == "company"
    assert active["source"] == "gdrive://source123"
    assert active["target"] == "gdrive://target456"
    assert active["archive"] == "archive789"


def test_run_lock_blocks_second_execution(tmp_path):
    lock_path = tmp_path / "run.lock"
    first = RunLock(lock_path)
    with first:
        second = RunLock(lock_path)
        try:
            with second:
                raise AssertionError("second execution should be blocked")
        except RuntimeError as exc:
            assert "already running" in str(exc)
