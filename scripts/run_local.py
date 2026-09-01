from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0].lower() if args else "run"

    if command == "regenerate":
        module_argv = args[1:]
        sys.argv = ["src.regeneration", *module_argv]
        namespace = runpy.run_module("src.regeneration", run_name="__main__")
        return int(namespace.get("__return_code__", 0))

    if command == "tts":
        module_argv = args[1:]
        sys.argv = ["src.tts_cli", *module_argv]
        namespace = runpy.run_module("src.tts_cli", run_name="__main__")
        return int(namespace.get("__return_code__", 0))

    if command in {"run", "reprocess-subtitles", "duplicates", "auth", "provider", "prefetch-whisper", "doctor", "init"}:
        main_argv = args
    else:
        main_argv = ["run", *args]

    sys.argv = ["main.py", *main_argv]
    namespace = runpy.run_module("main", run_name="__main__")
    return int(namespace.get("__return_code__", 0))


if __name__ == "__main__":
    raise SystemExit(main())
