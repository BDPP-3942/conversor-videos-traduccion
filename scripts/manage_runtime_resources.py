from __future__ import annotations

import argparse
import json

from src.cuda_runtime import inspect_cuda_runtime, install_managed_cuda_runtime, MANAGED_DIR
from src.local_translation import LocalTranslationModelManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect/remove managed local translation and CUDA resources")
    parser.add_argument("resource", choices=("translation-model", "cuda", "all"))
    parser.add_argument("action", choices=("status", "cleanup"))
    args = parser.parse_args()
    if args.resource in {"translation-model", "all"}:
        manager = LocalTranslationModelManager()
        if args.action == "status":
            status = manager.status()
            print(json.dumps({"resource": "translation-model", "available": status.available, "path": str(status.path), "reason": status.reason}, ensure_ascii=False, indent=2))
        else:
            manager.cleanup()
            print(f"removed={manager.model_dir}")
    if args.resource in {"cuda", "all"}:
        if args.action == "status":
            status = inspect_cuda_runtime()
            print(json.dumps({"resource": "cuda", "compatible": status.compatible, "nvidia_gpu": status.nvidia_gpu, "driver": status.driver_version, "toolkit": status.toolkit_version, "cuBLAS": status.cublas_version, "cuDNN": status.cudnn_version, "managed_path": str(MANAGED_DIR), "reason": status.reason}, ensure_ascii=False, indent=2))
        else:
            import shutil
            if MANAGED_DIR.exists() and not MANAGED_DIR.is_symlink():
                shutil.rmtree(MANAGED_DIR)
                print(f"removed={MANAGED_DIR}")
            else:
                print(f"managed_cuda_not_present={MANAGED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
