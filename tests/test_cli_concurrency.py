from __future__ import annotations

from pathlib import Path

import main
from config.settings import AppSettings


class _Readiness:
    ready = True
    checks = {"storage": "ok"}
    errors = []


class _Storage:
    def close(self):
        return None


class _Pipeline:
    received_settings = None

    def __init__(self, settings, storage):
        del storage
        type(self).received_settings = settings

    def run(self, source, target):
        del source, target
        return {"status": "success"}


def _args(tmp_path: Path, requested: int):
    source = tmp_path / "input"
    target = tmp_path / "output"
    source.mkdir()
    target.mkdir()
    settings = AppSettings(
        provider="local",
        source=f"local://{source}",
        target=f"local://{target}",
        auto_tune_resources=False,
        max_parallel_videos=0,
        automatic_output_deduplication=False,
    )
    parser = main.build_parser()
    args = parser.parse_args(["run", "--parallel-videos", str(requested)])
    return settings, args


def test_cli_override_is_clamped_before_pipeline_construction(monkeypatch, tmp_path: Path):
    settings, args = _args(tmp_path, 999)
    monkeypatch.setattr(main, "load_settings", lambda path: settings)
    monkeypatch.setattr(main, "check_unattended", lambda settings, ensure_rclone_binary=False: _Readiness())
    monkeypatch.setattr(main, "configure_logging", lambda level: None)
    monkeypatch.setattr(main, "create_storage_provider", lambda provider, settings: _Storage())
    monkeypatch.setattr(main, "safe_parallelism", lambda settings: 3)
    monkeypatch.setattr(main, "MediaPipeline", _Pipeline, raising=False)

    import src.pipeline

    monkeypatch.setattr(src.pipeline, "MediaPipeline", _Pipeline)

    assert main.command_run(args) == 0
    assert _Pipeline.received_settings.max_parallel_videos == 3


def test_cli_zero_preserves_auto_contract(monkeypatch, tmp_path: Path):
    settings, args = _args(tmp_path, 0)
    monkeypatch.setattr(main, "load_settings", lambda path: settings)
    monkeypatch.setattr(main, "check_unattended", lambda settings, ensure_rclone_binary=False: _Readiness())
    monkeypatch.setattr(main, "configure_logging", lambda level: None)
    monkeypatch.setattr(main, "create_storage_provider", lambda provider, settings: _Storage())
    monkeypatch.setattr(main, "safe_parallelism", lambda settings: 4)

    import src.pipeline

    monkeypatch.setattr(src.pipeline, "MediaPipeline", _Pipeline)

    assert main.command_run(args) == 0
    assert _Pipeline.received_settings.max_parallel_videos == 4
