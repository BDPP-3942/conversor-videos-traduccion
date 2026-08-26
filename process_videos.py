from __future__ import annotations

import argparse
import json

from config.loader import load_settings
from config.settings import ensure_directories
from src.raw_video_pipeline import RawVideoPipeline
from src.storage.factory import create_storage_provider
from src.storage.uri import parse_storage_uri


def main() -> int:
    parser = argparse.ArgumentParser(description="Process raw video files without ZIP containers")
    parser.add_argument("--source", default=None, help="Input folder URI; defaults to the active source")
    parser.add_argument("--target", default=None, help="Output folder URI; defaults to the active target")
    args = parser.parse_args()
    ensure_directories()
    settings = load_settings()
    source = args.source or settings.source
    target = args.target or settings.target
    provider = settings.provider.lower()
    storage = create_storage_provider(provider, settings)
    try:
        result = RawVideoPipeline(settings, storage).run(
            parse_storage_uri(source).value,
            parse_storage_uri(target).value,
        )
    finally:
        storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
