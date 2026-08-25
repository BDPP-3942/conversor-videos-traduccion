from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.output_deduplicator import OutputDeduplicator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local output duplicate management")
    parser.add_argument("--target", type=Path, default=Path("storage/output"))
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("scan", help="Detect duplicate output groups without modifying results")
    sub.add_parser("analyze", help="Analyze the most stable referente without deleting results")
    delete = sub.add_parser("delete", help="Delete only duplicates present in a previously analyzed plan")
    delete.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dedup = OutputDeduplicator(args.target)
    if args.action == "scan":
        payload = dedup.scan_and_persist()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.action == "analyze":
        payload = dedup.analyze_and_persist()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    results = dedup.delete(dry_run=args.dry_run)
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
