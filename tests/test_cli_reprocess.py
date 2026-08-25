from pathlib import Path

from main import build_parser


def test_reprocess_parser_accepts_scheduled_mode():
    args = build_parser().parse_args([
        "reprocess-subtitles",
        "--scheduled",
        "--output-folder",
        "37x02_Tema",
        "--translate-only",
    ])
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

    assert "reprocess-subtitles" in bat
    assert "reprocess-subtitles" in sh
    assert "reprocess-subtitles" in local_bat
    assert "reprocess-subtitles" in local_sh
    assert "reprocess-subtitles" in unattended_bat
    assert "reprocess-subtitles" in unattended_sh
    assert "run_unattended.bat %*" in scheduled_bat
    assert 'run_unattended.sh "$@"' in scheduled_sh
