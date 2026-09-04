from __future__ import annotations

import argparse
import json
import shutil

from src.cuda_runtime import MANAGED_DIR, inspect_cuda_runtime
from src.local_translation import LocalTranslationModelManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and remove project-managed optional runtime resources")
    parser.add_argument("resource", choices=("translation-model", "cuda", "all"))
    parser.add_argument("action", choices=("status", "cleanup"))
    args = parser.parse_args()

    if args.resource in {"translation-model", "all"}:
        manager = LocalTranslationModelManager()
        if args.action == "status":
            status = manager.status()
            payload = {
                "resource": "translation-model",
                "available": status.available,
                "path": str(status.path),
                "reason": status.reason,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            manager.cleanup()
            print(f"removed={manager.model_dir}")

    if args.resource in {"cuda", "all"}:
        if args.action == "status":
            status = inspect_cuda_runtime()
            payload = {
                "resource": "cuda",
                "compatible": status.compatible,
                "nvidia_gpu": status.nvidia_gpu,
                "driver": status.driver_version,
                "driver_cuda_max": status.driver_cuda_max,
                "toolkit": status.toolkit_version,
                "toolkit_path": status.toolkit_path,
                "cuBLAS": status.cublas_version,
                "cuDNN": status.cudnn_version,
                "faster_whisper": status.faster_whisper_version,
                "ctranslate2": status.ctranslate2_version,
                "managed_path": str(MANAGED_DIR),
                "reason": status.reason,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if MANAGED_DIR.exists() and not MANAGED_DIR.is_symlink():
                shutil.rmtree(MANAGED_DIR)
                print(f"removed={MANAGED_DIR}")
            else:
                print(f"managed_cuda_not_present={MANAGED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
