from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

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
    signature: tuple[str, ...]
    decision: str
    reason: str


class OutputDeduplicator:
    """Conservative three-phase deduplication for local output folders."""

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

    def __init__(self, root: Path, *, scan_state_path: Path | None = None, plan_path: Path | None = None) -> None:
        self.root = root.expanduser().resolve()
        state_dir = self.root.parent / "state"
        self.scan_state_path = (scan_state_path or state_dir / "dedupe_scan.json").resolve()
        self.plan_path = (plan_path or state_dir / "dedupe_plan.json").resolve()

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
            folders.append(OutputFolder(folder, folder.name, signature, score, tuple(reasons)))
        return folders

    def scan_and_persist(self) -> dict[str, Any]:
        folders = self.scan()
        payload = {
            "version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "root": str(self.root),
            "folders": [{"name": f.name, "signature": list(f.signature)} for f in folders],
        }
        self._atomic_write_json(self.scan_state_path, payload)
        return payload

    def analyze(self, scan: list[OutputFolder] | None = None) -> list[DuplicateDecision]:
        folders = scan if scan is not None else self._load_scan_folders()
        groups: dict[tuple[str, ...], list[OutputFolder]] = {}
        for folder in folders:
            groups.setdefault(folder.signature, []).append(folder)
        decisions: list[DuplicateDecision] = []
        for signature, candidates in groups.items():
            if len(candidates) < 2:
                continue
            ranked = sorted(candidates, key=lambda item: (-item.stability_score, item.name.casefold()))
            winner, next_best = ranked[0], ranked[1]
            if winner.stability_score <= next_best.stability_score:
                decisions.append(
                    DuplicateDecision(
                        canonical=winner,
                        duplicates=tuple(ranked[1:]),
                        signature=signature,
                        decision="keep",
                        reason="no uniquely more-stable result exists; nothing is safe to delete",
                    )
                )
                continue
            decisions.append(
                DuplicateDecision(
                    canonical=winner,
                    duplicates=tuple(ranked[1:]),
                    signature=signature,
                    decision="delete_duplicates",
                    reason=(
                        f"same generated resources; referente has a strictly higher stability score "
                        f"({winner.stability_score} > {next_best.stability_score})"
                    ),
                )
            )
        return decisions

    def analyze_and_persist(self, scan: list[OutputFolder] | None = None) -> dict[str, Any]:
        decisions = self.analyze(scan)
        payload = {
            "version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "root": str(self.root),
            "scan_file": str(self.scan_state_path),
            "groups": [self._decision_to_json(d) for d in decisions],
            "deletions": [
                {
                    "canonical": d.canonical.name,
                    "canonical_score": d.canonical.stability_score,
                    "duplicate": duplicate.name,
                    "duplicate_score": duplicate.stability_score,
                    "signature": list(d.signature),
                    "reason": d.reason,
                }
                for d in decisions
                if d.decision == "delete_duplicates"
                for duplicate in d.duplicates
            ],
        }
        self._atomic_write_json(self.plan_path, payload)
        return payload

    def delete(self, *, dry_run: bool = False) -> list[dict[str, Any]]:
        plan = self._load_json(self.plan_path)
        if plan.get("root") != str(self.root):
            raise RuntimeError("Deduplication plan belongs to a different output root")
        results: list[dict[str, Any]] = []
        deleted_names: list[str] = []
        for item in plan.get("deletions", []):
            canonical_name = str(item.get("canonical", ""))
            duplicate_name = str(item.get("duplicate", ""))
            signature = tuple(str(value) for value in item.get("signature", []))
            reason = str(item.get("reason", ""))
            validation_error = self._validate_delete_candidate(canonical_name, duplicate_name, signature)
            if validation_error:
                results.append({"status": "skipped", "canonical": canonical_name, "duplicate": duplicate_name, "reason": validation_error})
                continue
            result = {
                "status": "planned" if dry_run else "deleted",
                "canonical": canonical_name,
                "duplicate": duplicate_name,
                "canonical_score": int(item.get("canonical_score", 0)),
                "duplicate_score": int(item.get("duplicate_score", 0)),
                "reason": reason,
            }
            if not dry_run:
                shutil.rmtree(self.root / duplicate_name)
                deleted_names.append(duplicate_name)
            results.append(result)
        if deleted_names and not dry_run:
            self._remove_deleted_state(deleted_names)
        return results

    # Compatibility with the previous API.
    def find_decisions(self) -> list[DuplicateDecision]:
        return self.analyze(self.scan())

    def apply(self, *, dry_run: bool = False) -> list[dict[str, Any]]:
        self.scan_and_persist()
        self.analyze_and_persist()
        return self.delete(dry_run=dry_run)

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

    def _validate_delete_candidate(self, canonical_name: str, duplicate_name: str, expected_signature: tuple[str, ...]) -> str | None:
        if not canonical_name or not duplicate_name:
            return "invalid deletion plan entry"
        if canonical_name == duplicate_name:
            return "refusing to delete the referente itself"
        canonical = self._safe_child(canonical_name)
        duplicate = self._safe_child(duplicate_name)
        if canonical is None or duplicate is None:
            return "invalid output path in deletion plan"
        if not canonical.is_dir():
            return "referente no longer exists"
        if not duplicate.is_dir():
            return "duplicate no longer exists"
        if self._content_signature(canonical) != expected_signature:
            return "referente content changed since analysis"
        if self._content_signature(duplicate) != expected_signature:
            return "duplicate content changed since analysis"
        return None

    def _safe_child(self, name: str) -> Path | None:
        candidate = (self.root / name).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        return candidate if candidate.parent == self.root else None

    def _load_scan_folders(self) -> list[OutputFolder]:
        payload = self._load_json(self.scan_state_path)
        if payload.get("root") != str(self.root):
            raise RuntimeError("Deduplication scan belongs to a different output root")
        result: list[OutputFolder] = []
        for item in payload.get("folders", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            signature = tuple(str(value) for value in item.get("signature", []))
            path = self._safe_child(name)
            if name and signature and path is not None:
                score, reasons = self.name_stability(name)
                result.append(OutputFolder(path, name, signature, score, tuple(reasons)))
        return result

    def _remove_deleted_state(self, deleted_names: Iterable[str]) -> None:
        deleted = set(deleted_names)
        registry_path = self.root.parent / "state" / "media_registry.jsonl"
        history_path = self.root.parent / "state" / "dedupe_history.jsonl"
        removed_registry: list[dict[str, Any]] = []
        if registry_path.is_file():
            kept: list[str] = []
            for line in registry_path.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    kept.append(line)
                    continue
                if isinstance(item, dict) and item.get("output_folder") in deleted:
                    removed = dict(item)
                    removed["status"] = "dedupe_removed"
                    removed_registry.append(removed)
                else:
                    kept.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
            registry_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        manifest_updates: list[dict[str, Any]] = []
        manifests = self.root / "_manifests"
        if manifests.is_dir():
            from src.manifest import read_manifest, write_manifest
            for manifest_path in manifests.glob("*.json"):
                data = read_manifest(manifest_path)
                entries = data.get("entries", [])
                if not isinstance(entries, list):
                    continue
                kept_entries = [entry for entry in entries if not (isinstance(entry, dict) and entry.get("output_folder") in deleted)]
                removed_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("output_folder") in deleted]
                if removed_entries:
                    write_manifest(manifest_path, kept_entries, metadata=data.get("metadata", {}))
                    manifest_updates.extend({"manifest": manifest_path.name, "entry": entry} for entry in removed_entries)
        if removed_registry or manifest_updates:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with history_path.open("a", encoding="utf-8") as handle:
                for item in removed_registry:
                    handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
                for item in manifest_updates:
                    handle.write(json.dumps({"status": "dedupe_manifest_entry_removed", **item}, ensure_ascii=False, separators=(",", ":")) + "\n")

    @staticmethod
    def _content_signature(folder: Path) -> tuple[str, ...]:
        hashes: list[str] = []
        for path in sorted((candidate for candidate in folder.rglob("*") if candidate.is_file()), key=lambda item: item.relative_to(folder).as_posix().casefold()):
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
    def _decision_to_json(decision: DuplicateDecision) -> dict[str, Any]:
        return {
            "decision": decision.decision,
            "reason": decision.reason,
            "signature": list(decision.signature),
            "referente": {
                "name": decision.canonical.name,
                "stability_score": decision.canonical.stability_score,
                "stability_reasons": list(decision.canonical.stability_reasons),
            },
            "duplicates": [
                {"name": duplicate.name, "stability_score": duplicate.stability_score, "stability_reasons": list(duplicate.stability_reasons)}
                for duplicate in decision.duplicates
            ],
        }

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"Deduplication state file not found: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"Invalid deduplication state file: {path}")
        return value

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
