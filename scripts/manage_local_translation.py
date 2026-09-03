from __future__ import annotations

import argparse

from src.local_translation import LocalTranslationModelManager


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage the pinned offline local translation model"
    )
    parser.add_argument("action", choices=("status", "download", "cleanup"))
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm the model download without an interactive prompt",
    )
    args = parser.parse_args()

    manager = LocalTranslationModelManager()
    status = manager.status()
    if args.action == "status":
        print(f"available={status.available}")
        print(f"resource={status.repository}@{status.revision}")
        print(f"license={status.license}")
        print(f"destination={status.path}")
        print(f"approximate_size_mib={status.expected_size_bytes / 1024**2:.1f}")
        if status.reason:
            print(f"reason={status.reason}")
        return 0 if status.available else 1

    if args.action == "cleanup":
        manager.cleanup()
        print(f"removed={manager.model_dir}")
        return 0

    if status.available:
        print(f"already_available={status.path}")
        return 0
    print(f"Resource: {status.repository}@{status.revision}")
    print(f"Version/revision: {status.revision}")
    print(f"Approximate size: {status.expected_size_bytes / 1024**2:.1f} MiB")
    print(f"Destination: {status.path}")
    print("Reason: prepare the local translation provider for offline processing")
    print(f"License: {status.license}")
    if not args.yes:
        answer = input("Download this resource now? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Download cancelled.")
            return 2
    manager.download()
    final = manager.status()
    if not final.available:
        print(f"Download completed but validation failed: {final.reason}")
        return 1
    print(f"ready={final.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
