from __future__ import annotations

import pytest

from main import build_parser as build_main_parser
from src.cli_run_options import REGENERATE_RUN_OPTIONS, RUN_ONLY_OPTIONS
from src.regeneration import build_parser


def _run_option_names() -> set[str]:
    parser = build_main_parser()
    run_parser = parser._subparsers._group_actions[0].choices["run"]
    return {
        option
        for action in run_parser._actions
        for option in action.option_strings
        if option not in {"-h", "--help"}
    }


def test_every_run_option_is_classified_for_regeneration() -> None:
    run_options = _run_option_names()
    classified = REGENERATE_RUN_OPTIONS | RUN_ONLY_OPTIONS
    assert run_options - classified == set()


def test_regeneration_accepts_all_shared_run_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--provider",
            "local",
            "--source",
            "local://storage/input",
            "--target",
            "local://storage/output",
            "--no-name-migration",
            "--parallel-videos",
            "2",
            "--translation-batch-size",
            "8",
            "--whisper-beam-size",
            "3",
            "--whisper-cpu-threads",
            "4",
            "--no-ffmpeg-copy",
            "--generate-webm",
        ]
    )

    assert args.provider == "local"
    assert args.source == "local://storage/input"
    assert args.target == "local://storage/output"
    assert args.no_name_migration is True
    assert args.parallel_videos == 2
    assert args.translation_batch_size == 8
    assert args.whisper_beam_size == 3
    assert args.whisper_cpu_threads == 4
    assert args.no_ffmpeg_copy is True
    assert args.generate_webm is True


def test_regeneration_preserves_run_webm_override_default() -> None:
    args = build_parser().parse_args([])
    assert args.generate_webm is None


def test_regeneration_reuses_run_help_contract() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    for option in REGENERATE_RUN_OPTIONS:
        assert option in help_text

    assert "Force generation of the secondary WebM output" in help_text
    assert "Prevent generation of the secondary WebM output" in help_text


def test_run_only_options_are_not_accepted_by_regeneration() -> None:
    parser = build_parser()

    for option in RUN_ONLY_OPTIONS:
        with pytest.raises(SystemExit):
            parser.parse_args([option])


def test_webm_options_remain_mutually_exclusive() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--generate-webm", "--no-webm"])
