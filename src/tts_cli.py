from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from config.loader import load_settings
from config.settings import BASE_DIR, resolve_project_path
from src.tts_pipeline import TTSProviderError, generate_tts_media

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synchronized TTS media from translated VTT outputs")
    parser.add_argument("--config", type=Path, default=BASE_DIR / "config" / "app.toml")
    parser.add_argument("--output-folder", default=None, help="Existing output folder to process")
    parser.add_argument("--all", action="store_true", help="Process all eligible local output folders")
    parser.add_argument("--no-webm", action="store_true", help="Skip TTS WebM even when WebM is configured")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    if args.no_webm:
        from dataclasses import replace

        settings = replace(settings, tts_generate_webm=False)
    if not args.output_folder and not args.all:
        raise SystemExit("Indica --output-folder o --all")

    root = resolve_project_path("storage/output")
    folders = [root / args.output_folder] if args.output_folder else sorted(p for p in root.iterdir() if p.is_dir() and p.name != "_manifests")
    results: list[dict[str, object]] = []
    for folder in folders:
        result = _process_folder(folder, settings)
        results.append(result)
    print(json.dumps({"status": "success", "results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "success" for item in results) else 2


def _process_folder(folder: Path, settings) -> dict[str, object]:
    if not folder.is_dir():
        return {"folder": str(folder), "status": "error", "error": "output folder does not exist"}
    video = next((p for p in folder.glob("*.mp4") if "_tts" not in p.stem.lower()), None)
    vtt = next((p for p in folder.glob("*.vtt") if "_original" not in p.name.lower()), None)
    webm = next((p for p in folder.glob("*.webm") if "_tts" not in p.stem.lower()), None)
    if not video or not vtt:
        return {"folder": str(folder), "status": "skipped", "reason": "MP4 or translated VTT not found"}
    try:
        result = generate_tts_media(
            video,
            vtt,
            folder,
            video.stem,
            settings,
            webm_video_path=webm,
        )
    except (TTSProviderError, RuntimeError, ValueError, OSError) as exc:
        logger.exception("TTS generation failed for %s", folder)
        return {"folder": str(folder), "status": "error", "error": str(exc)}
    return {
        "folder": str(folder),
        "status": "success",
        "mp4": result.mp4_path.name,
        "webm": result.webm_path.name if result.webm_path else None,
        "audio": result.audio_path.name,
        "cues": result.cue_count,
        "adjusted_cues": result.adjusted_cues,
    }


if __name__ == "__main__":
    raise SystemExit(main())
