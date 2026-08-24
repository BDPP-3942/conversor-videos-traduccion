from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OutputFolder:
    path: Path
    name: str
    signature: tuple[str, ...]
    stability_score: int
    stability_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DuplicateDecision:
    canonical: OutputFolder
    duplicates: tuple[OutputFolder, ...]
    reason: str


class OutputDeduplicator:
    """Find and optionally remove exact output-folder duplicates conservatively.

    Folder identity is based on the SHA-256 multiset of every generated file in the
    folder, not on filenames. This makes two runs with different output stems match
    when their actual generated resources are identical. A folder is only eligible
    for deletion when another folder in the same identity group has a strictly more
    stable output name. Ties remain untouched.
    """

    _CANONICAL_PATTERN = re.compile(r"^\d{1,4}x\d{2}(?:_.+)?$", re.IGNORECASE)
    _NUMERIC_COURSE_LESSON_PATTERN = re.compile(r"^\d{1,4}x\d{2}(?:_.+)?$")
    _PARTIAL_NUMERIC_PATTERN = re.compile(r"^(?:\d{1,4}x(?:\d{2})?|(?:\d{1,4})?x\d{2})(?:_.+)?$")
    _HASH_SUFFIX_PATTERN = re.compile(r"(?:^|[_-])[0-9a-f]{8,}(?:$|[_-])", re.IGNORECASE)
    _TIMESTAMP_PATTERN = re.compile(r"20\d{6}t\d{4,6}z(?:[-_]\d+[-_]\d+)?", re.IGNORECASE)
    _NOISE_PATTERN = re.compile(
        r"(?:^|[_-])(wetransfer|drive-download|archive|compressed|backup|download|descarga)(?:$|[_-])",
        re.IGNORECASE,
    )
    _PLACEHOLDER_PATTERN = re.compile(r"(?:^|[_-])(?:sin_curso|sin_leccion|sin_nombre)(?:$|[_-])", re.IGNORECASE)
    _COPY_PATTERN = re.compile(r"(?:^|[_ -])(?:copy|copia|\(?\d+\)?)(?:$|[_ -])", re.IGNORECASE)

    def __init__(self, root: Path, *, dry_run: bool = True) -> None:
        self.root = root.expanduser().resolve()
        self.dry_run = dry_run

    def scan(self) -> list[OutputFolder]:
        if not self.root.is_dir():
            raise FileNotFoundError(f"Output directory does not exist: {self.root}")
        folders: list[OutputFolder] = []
        for folder in sorted(self.root.iterdir(), key=lambda item: item.name.casefold()):
            if not folder.is_dir() or folder.name == "_manifests":
                continue
            signature = self._content_signature(folder)
            if not signature:
                continue
            score, reasons = self.name_stability(folder.name)
            folders.append(
                OutputFolder(
                    path=folder,
                    name=folder.name,
                    signature=signature,
                    stability_score=score,
                    stability_reasons=tuple(reasons),
                )
            )
        return folders

    def find_decisions(self) -> list[DuplicateDecision]:
        groups: dict[tuple[str, ...], list[OutputFolder]] = {}
        for folder in self.scan():
            groups.setdefault(folder.signature, []).append(folder)

        decisions: list[DuplicateDecision] = []
        for candidates in groups.values():
            if len(candidates) < 2:
                continue
            ranked = sorted(candidates, key=lambda item: (-item.stability_score, item.name.casefold()))
            winner = ranked[0]
            next_best = ranked[1]
            if winner.stability_score <= next_best.stability_score:
                logger.info(
                    "Duplicate group kept unchanged because no uniquely more-stable name exists: %s",
                    ", ".join(item.name for item in candidates),
                )
                continue
            decisions.append(
                DuplicateDecision(
                    canonical=winner,
                    duplicates=tuple(item for item in ranked[1:]),
                    reason=(
                        f"canonical score {winner.stability_score} > next score {next_best.stability_score}; "
                        f"{winner.name}: {', '.join(winner.stability_reasons)}"
                    ),
                )
            )
        return decisions

    def apply(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        history_path = self.root.parent / "state" / "dedupe_history.jsonl"
        deleted_names: list[str] = []
        for decision in self.find_decisions():
            logger.info(
                "Canonical output: %s; candidates for removal: %s",
                decision.canonical.name,
                ", ".join(item.name for item in decision.duplicates),
            )
            for duplicate in decision.duplicates:
                item = {
                    "status": "planned" if self.dry_run else "deleted",
                    "canonical": decision.canonical.name,
                    "duplicate": duplicate.name,
                    "score": duplicate.stability_score,
                    "canonical_score": decision.canonical.stability_score,
                    "reason": decision.reason,
                }
                if self.dry_run:
                    results.append(item)
                    continue
                shutil.rmtree(duplicate.path)
                deleted_names.append(duplicate.name)
                results.append(item)

        if deleted_names:
            self._remove_deleted_registry_entries(deleted_names, history_path)
        return results

    @classmethod
    def name_stability(cls, name: str) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        lowered = name.casefold()

        if cls._NUMERIC_COURSE_LESSON_PATTERN.fullmatch(name):
            score += 100
            reasons.append("canonical course x lesson structure")
        elif cls._PARTIAL_NUMERIC_PATTERN.fullmatch(name):
            score += 70
            reasons.append("partially numeric course/lesson structure")
        elif cls._CANONICAL_PATTERN.search(name):
            score += 55
            reasons.append("structured course x lesson prefix")
        else:
            reasons.append("no canonical course x lesson structure")

        if cls._PLACEHOLDER_PATTERN.search(lowered):
            score -= 45
            reasons.append("contains unresolved placeholder")
        if cls._NOISE_PATTERN.search(lowered):
            score -= 35
            reasons.append("contains download/compression noise")
        if cls._TIMESTAMP_PATTERN.search(lowered):
            score -= 25
            reasons.append("contains download timestamp")
        if cls._HASH_SUFFIX_PATTERN.search(lowered):
            score -= 20
            reasons.append("contains generated hash-like suffix")
        if cls._COPY_PATTERN.search(lowered):
            score -= 15
            reasons.append("contains copy/numbered-copy suffix")

        if len(name) <= 80:
            score += 5
            reasons.append("compact output name")
        elif len(name) > 140:
            score -= 10
            reasons.append("excessively long output name")

        return score, reasons

    @staticmethod
    def _content_signature(folder: Path) -> tuple[str, ...]:
        hashes: list[str] = []
        for path in sorted(
            (candidate for candidate in folder.rglob("*") if candidate.is_file()),
            key=lambda item: item.relative_to(folder).as_posix().casefold(),
        ):
            relative = path.relative_to(folder)
            if relative.parts and relative.parts[0] == "_manifests":
                continue
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            hashes.append(digest.hexdigest())
        return tuple(sorted(hashes))

    @staticmethod
    def _remove_deleted_registry_entries(deleted_names: Iterable[str], history_path: Path) -> None:
        from config.settings import STORAGE_DIR

        registry_path = STORAGE_DIR / "state" / "media_registry.jsonl"
        deleted = set(deleted_names)
        if not registry_path.is_file():
            return
        kept: list[str] = []
        removed: list[dict[str, object]] = []
        for line in registry_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                kept.append(line)
                continue
            if isinstance(item, dict) and item.get("output_folder") in deleted:
                item["status"] = "dedupe_removed"
                removed.append(item)
                continue
            kept.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
        registry_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")

        if removed:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with history_path.open("a", encoding="utf-8") as handle:
                for item in removed:
                    handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
