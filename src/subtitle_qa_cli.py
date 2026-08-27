from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.subtitle_qa import run_subtitle_qa


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check and optionally correct a WebVTT subtitle file")
    parser.add_argument("vtt", type=Path, help="Translated VTT to review")
    parser.add_argument("--source-vtt", type=Path, default=None, help="Original/source VTT for contextual comparison")
    parser.add_argument("--engine", choices=["languagetool", "ollama", "both"], default="languagetool")
    parser.add_argument("--auto-correct", action="store_true", help="Write corrections to --output-vtt")
    parser.add_argument("--output-vtt", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None, help="Write a JSON QA report")
    parser.add_argument("--language", default="en-US", help="LanguageTool language code")
    parser.add_argument("--languagetool-url", default="http://127.0.0.1:8081/v2/check")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434/api/chat")
    parser.add_argument("--ollama-model", default="qwen3:8b")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_subtitle_qa(
        args.vtt,
        engine=args.engine,
        source_vtt=args.source_vtt,
        output_path=args.output_vtt,
        report_path=args.report,
        auto_correct=args.auto_correct,
        languagetool_url=args.languagetool_url,
        languagetool_language=args.language,
        ollama_url=args.ollama_url,
        ollama_model=args.ollama_model,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"clean", "changes"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
