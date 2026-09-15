from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.subtitle_qa import run_subtitle_qa


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comprueba y, opcionalmente, corrige un archivo de subtítulos WebVTT"
    )
    parser.add_argument("vtt", type=Path, help="Archivo VTT traducido que se va a revisar")
    parser.add_argument(
        "--source-vtt",
        type=Path,
        default=None,
        help="Archivo VTT original para comparación contextual",
    )
    parser.add_argument(
        "--engine",
        choices=["languagetool", "ollama", "both"],
        default="languagetool",
        help="Motor de QA que se utilizará: LanguageTool, Ollama o ambos",
    )
    parser.add_argument(
        "--auto-correct",
        action="store_true",
        help="Escribe las correcciones en --output-vtt",
    )
    parser.add_argument(
        "--output-vtt",
        type=Path,
        default=None,
        help="Ruta del VTT corregido",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Escribe un informe JSON del control de calidad",
    )
    parser.add_argument(
        "--language",
        default="en-US",
        help="Código de idioma que utilizará LanguageTool",
    )
    parser.add_argument(
        "--languagetool-url",
        default="http://127.0.0.1:8081/v2/check",
        help="URL del servicio LanguageTool",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://127.0.0.1:11434/api/chat",
        help="URL de la API de Ollama",
    )
    parser.add_argument(
        "--ollama-model",
        default="qwen3:8b",
        help="Modelo de Ollama utilizado para la revisión",
    )
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
