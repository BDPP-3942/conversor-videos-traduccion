from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0].lower() if args else "run"

    if command == "regenerate":
        from src.regeneration import main as regeneration_main

        return int(regeneration_main(args[1:]))

    if command == "tts":
        from src.tts_cli import main as tts_main

        return int(tts_main(args[1:]))

    supported_commands = {
        "run",
        "reprocess-subtitles",
        "duplicates",
        "auth",
        "provider",
        "prefetch-whisper",
        "doctor",
        "init",
    }
    if command in supported_commands:
        main_argv = args
    else:
        main_argv = ["run", *args]

    from main import main as application_main

    original_argv = sys.argv
    try:
        sys.argv = ["main.py", *main_argv]
        return int(application_main())
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
