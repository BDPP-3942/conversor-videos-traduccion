from __future__ import annotations

import json
import sys

import main
from config.settings import AppSettings


def test_e2e_cli_dry_run_contract(monkeypatch, capsys):
    class Readiness:
        ready = True
        checks = {"storage": "ok"}
        errors = []

    settings = AppSettings(
        provider="local",
        source="local://input",
        target="local://output",
        auto_update_rclone=False,
        auto_bootstrap_rclone=False,
    )
    monkeypatch.setattr(main, "load_settings", lambda path: settings)
    monkeypatch.setattr(main, "check_unattended", lambda settings, ensure_rclone_binary=False: Readiness())
    monkeypatch.setattr(main, "configure_logging", lambda level: None)
    monkeypatch.setattr(sys, "argv", ["video-translation-pipeline", "run", "--dry-run"])

    assert main.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["provider"] == "local"


def test_e2e_entrypoint_parser_exposes_concurrency_override():
    args = main.build_parser().parse_args(["run", "--parallel-videos", "999"])
    assert args.parallel_videos == 999
