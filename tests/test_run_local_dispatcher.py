from __future__ import annotations

import sys
from unittest.mock import patch

from scripts.run_local import main


def test_run_local_explicit_run_preserves_arguments() -> None:
    with patch("main.main", return_value=0) as application:
        assert main(["run", "--config", "config/app.toml", "--no-webm"]) == 0
    application.assert_called_once_with()


def test_run_local_implicit_run_preserves_arguments() -> None:
    observed_argv: list[list[str]] = []

    def _application_main() -> int:
        observed_argv.append(sys.argv.copy())
        return 0

    with patch("main.main", side_effect=_application_main) as application:
        assert main(["--config", "config/app.toml", "--no-webm"]) == 0

    assert observed_argv == [["main.py", "run", "--config", "config/app.toml", "--no-webm"]]
    application.assert_called_once_with()


def test_run_local_regenerate_removes_only_wrapper_subcommand() -> None:
    with patch("src.regeneration.main", return_value=0) as regeneration:
        assert main(["regenerate", "--config", "config/app.toml", "--no-webm"]) == 0
    regeneration.assert_called_once_with(["--config", "config/app.toml", "--no-webm"])


def test_run_local_tts_removes_only_wrapper_subcommand() -> None:
    with patch("src.tts_cli.main", return_value=0) as tts:
        assert main(["tts", "--help"]) == 0
    tts.assert_called_once_with(["--help"])
