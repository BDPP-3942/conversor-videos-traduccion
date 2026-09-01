from __future__ import annotations

import pytest

from src.cli_run_options import REGENERATE_RUN_OPTIONS, RUN_ONLY_OPTIONS
from src.regeneration import build_parser


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

    assert "Generate the secondary WebM output" in help_text
    assert "Do not generate the secondary WebM output" in help_text


def test_run_only_options_are_not_accepted_by_regeneration() -> None:
    parser = build_parser()

    for option in RUN_ONLY_OPTIONS:
        with pytest.raises(SystemExit):
            parser.parse_args([option])


def test_webm_options_remain_mutually_exclusive() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--generate-webm", "--no-webm"])
