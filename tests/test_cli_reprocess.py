from pathlib import Path

from main import build_parser


def test_reprocess_parser_accepts_scheduled_mode():
    args = build_parser().parse_args(["reprocess-subtitles", "--scheduled", "--output-folder", "37x02_Tema", "--translate-only"])
    assert args.command == "reprocess-subtitles"
    assert args.scheduled is True
    assert args.translate_only is True


def test_reprocess_wrappers_exist_and_dispatch_to_reprocess_command():
    root = Path(__file__).parents[1]
    bat = (root / "scripts" / "reprocess_subtitles.bat").read_text(encoding="utf-8")
    sh = (root / "scripts" / "reprocess_subtitles.sh").read_text(encoding="utf-8")
    local_bat = (root / "scripts" / "run_local.bat").read_text(encoding="utf-8")
    local_sh = (root / "scripts" / "run_local.sh").read_text(encoding="utf-8")
    unattended_bat = (root / "scripts" / "run_unattended.bat").read_text(encoding="utf-8")
    unattended_sh = (root / "scripts" / "run_unattended.sh").read_text(encoding="utf-8")
    scheduled_bat = (root / "scripts" / "run_scheduled.bat").read_text(encoding="utf-8")
    scheduled_sh = (root / "scripts" / "run_scheduled.sh").read_text(encoding="utf-8")
    assert "reprocess-subtitles" in bat and "reprocess-subtitles" in sh
    assert "reprocess-subtitles" in local_bat and "reprocess-subtitles" in local_sh
    assert "reprocess-subtitles" in unattended_bat and "reprocess-subtitles" in unattended_sh
    assert "run_unattended.bat %*" in scheduled_bat
    assert 'run_unattended.sh "$@"' in scheduled_sh


def test_local_wrappers_dispatch_duplicates_without_adding_run_command():
    root = Path(__file__).parents[1]
    local_bat = (root / "scripts" / "run_local.bat").read_text(encoding="utf-8")
    local_sh = (root / "scripts" / "run_local.sh").read_text(encoding="utf-8")
    assert '"%~1"=="duplicates"' in local_bat
    assert '"${1:-}" == "duplicates"' in local_sh


def test_duplicates_parser_supports_scan_analyze_and_delete_dry_run():
    parser = build_parser()
    assert parser.parse_args(["duplicates", "scan"]).duplicates_command == "scan"
    assert parser.parse_args(["duplicates", "analyze"]).duplicates_command == "analyze"
    args = parser.parse_args(["duplicates", "delete", "--dry-run"])
    assert args.duplicates_command == "delete"
    assert args.dry_run is True


def test_run_parser_accepts_webm_toggle():
    args = build_parser().parse_args(["run", "--no-webm"])
    assert args.command == "run"
    assert args.generate_webm is False
    args = build_parser().parse_args(["run", "--generate-webm"])
    assert args.generate_webm is True


def test_run_webm_flags_are_mutually_exclusive():
    import pytest
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--no-webm", "--generate-webm"])
