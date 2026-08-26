from __future__ import annotations

import argparse
import json

from config.loader import load_settings
from config.settings import ensure_directories
from src.raw_video_pipeline_v2 import RawVideoPipeline
from src.storage.factory import create_storage_provider
from src.storage.uri import parse_storage_uri


def main() -> int:
    parser = argparse.ArgumentParser(description="Process raw video files without ZIP containers")
    parser.add_argument("--source", default=None)
    parser.add_argument("--target", default=None)
    args = parser.parse_args()
    ensure_directories()
    settings = load_settings()
    storage = create_storage_provider(settings.provider.lower(), settings)
    try:
        result = RawVideoPipeline(settings, storage).run(
            parse_storage_uri(args.source or settings.source).value,
            parse_storage_uri(args.target or settings.target).value,
        )
    finally:
        storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
