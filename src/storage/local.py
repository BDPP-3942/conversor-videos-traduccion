from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any

from config.settings import resolve_project_path
from src.file_naming import normalize_component
from src.path_limits import fit_component
from src.storage.base import StorageFile, StorageProvider
from src.storage.processed_registry import ProcessedRegistry, sha256_file

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """Proveedor local. La configuración por defecto usa ./storage del proyecto."""

    def __init__(self, retain_sources: bool = False, input_min_age_seconds: int = 0):
        self.retain_sources = retain_sources
        self.input_min_age_seconds = input_min_age_seconds

    def _folder(self, target: str) -> Path:
        return resolve_project_path(target)

    def _storage_root(self, target: str) -> Path:
        return self._folder(target)

    def list_zip_files(self, target: str) -> list[StorageFile]:
        folder = self._folder(target)
        if not folder.is_dir():
            return []
        now = time.time()
        result = []
        for path in sorted(folder.rglob("*.zip"), key=lambda item: str(item).lower()):
            if not path.is_file():
                continue
            if self.input_min_age_seconds > 0 and now - path.stat().st_mtime < self.input_min_age_seconds:
                continue
            result.append(StorageFile(id=str(path), name=path.name, is_directory=False))
        return result

    def download_file(self, file: StorageFile, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file.id, destination)

    def upload_file(self, source: Path, target: str, content_type: str | None = None) -> str:
        del content_type
        folder = self._folder(target)
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / source.name
        shutil.copy2(source, destination)
        return str(destination)

    def create_folder(self, parent: str, name: str) -> str:
        folder = self._folder(parent) / name
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)

    def folder_exists(self, parent: str, name: str) -> bool:
        return (self._folder(parent) / name).is_dir()

    def file_exists(self, parent: str, name: str) -> bool:
        return (self._folder(parent) / name).is_file()

    def list_children(self, parent: str) -> list[StorageFile]:
        folder = self._folder(parent)
        return [
            StorageFile(id=str(child), name=child.name, is_directory=child.is_dir())
            for child in sorted(folder.iterdir(), key=lambda item: item.name.lower())
        ]

    def delete_folder(self, parent: str, name: str) -> None:
        folder = self._folder(parent) / name
        if folder.is_dir():
            shutil.rmtree(folder)

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        root = self._folder(target)
        old = root / old_name
        new = root / new_name
        if not old.is_dir():
            return {}
        if new.exists() and new != old:
            raise FileExistsError(f"Output target already exists: {new}")
        old.rename(new)
        mapping = {old_name: new_name}
        old_stem = normalize_component(old_name)
        new_stem = normalize_component(new_name)
        try:
            for child in sorted(new.iterdir(), key=lambda item: item.name.lower()):
                if child.is_dir():
                    if child.name == original_transcript_subdir:
                        for nested in sorted(child.iterdir(), key=lambda item: item.name.lower()):
                            if not nested.is_file():
                                continue
                            normalized_stem = normalize_component(nested.stem)
                            if normalized_stem.startswith(old_stem):
                                desired_stem = new_stem + normalized_stem[len(old_stem) :]
                            else:
                                desired_stem = normalized_stem
                            desired = fit_component(desired_stem, child) + nested.suffix.lower()
                            if desired != nested.name and not (child / desired).exists():
                                nested.rename(child / desired)
                        continue
                    continue
                normalized_stem = normalize_component(child.stem)
                if normalized_stem.startswith(old_stem):
                    desired_stem = new_stem + normalized_stem[len(old_stem) :]
                else:
                    desired_stem = normalized_stem
                desired = f"{fit_component(desired_stem, new)}{child.suffix.lower()}"
                if desired != child.name and not (new / desired).exists():
                    child.rename(new / desired)
        except FileNotFoundError:
            logger.warning("Output disappeared during rename-only migration: %s", old)
        self._update_manifests_after_migration(root, mapping)
        return mapping

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        root = self._folder(target)
        mapping: dict[str, str] = {}
        for folder in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if not folder.is_dir() or folder.name == "_manifests":
                continue
            old_rel = folder.relative_to(root).as_posix()
            new_name = fit_component(normalize_component(folder.name), root)
            if new_name != folder.name:
                candidate = root / new_name
                if candidate.exists():
                    logger.warning(
                        "Cannot normalize output folder '%s' because '%s' already exists",
                        folder.name,
                        candidate.name,
                    )
                else:
                    try:
                        folder.rename(candidate)
                        mapping[old_rel] = candidate.relative_to(root).as_posix()
                        folder = candidate
                    except FileNotFoundError:
                        logger.warning("Output folder disappeared during normalization: %s", folder)
                        continue
            self._normalize_files_recursive(folder, root, original_transcript_subdir, mapping)
        self._update_manifests_after_migration(root, mapping)
        return mapping

    def _normalize_files_recursive(
        self, root: Path, storage_root: Path, original_transcript_subdir: str, mapping: dict[str, str]
    ) -> None:
        try:
            children = list(root.iterdir())
        except FileNotFoundError:
            return
        for child in children:
            old_rel = child.relative_to(storage_root).as_posix()
            if child.is_dir():
                if child.name == original_transcript_subdir:
                    self._normalize_files_recursive(child, storage_root, original_transcript_subdir, mapping)
                    continue
                normalized = fit_component(normalize_component(child.name), child.parent)
                if normalized != child.name:
                    target = child.with_name(normalized)
                    if not target.exists():
                        try:
                            child.rename(target)
                            mapping[old_rel] = target.relative_to(storage_root).as_posix()
                            child = target
                        except FileNotFoundError:
                            continue
                self._normalize_files_recursive(child, storage_root, original_transcript_subdir, mapping)
                continue
            normalized_stem = fit_component(normalize_component(child.stem), child.parent)
            normalized_name = f"{normalized_stem}{child.suffix.lower()}"
            if normalized_name == child.name:
                continue
            target = child.with_name(normalized_name)
            if target.exists():
                logger.warning("Cannot normalize file '%s': '%s' already exists", child, target)
                continue
            try:
                child.rename(target)
                mapping[old_rel] = target.relative_to(storage_root).as_posix()
            except FileNotFoundError:
                logger.warning("Output file disappeared during normalization: %s", child)

    def _update_manifests_after_migration(self, root: Path, mapping: dict[str, str]) -> None:
        manifests = root / "_manifests"
        if not manifests.is_dir() or not mapping:
            return
        from src.manifest import read_manifest, write_manifest

        for manifest in manifests.glob("*.json"):
            data = read_manifest(manifest)
            changed = False
            for entry in data.get("entries", []):
                if not isinstance(entry, dict):
                    continue
                old_folder = str(entry.get("output_folder", ""))
                if not old_folder:
                    continue
                new_folder = Path(mapping.get(old_folder, old_folder)).name
                output_dir = root / new_folder
                if new_folder != old_folder:
                    entry["output_folder"] = new_folder
                    changed = True
                for key in ("video", "secondary_video", "audio", "translated_vtt"):
                    old_name = str(entry.get(key, ""))
                    if not old_name:
                        continue
                    candidate = output_dir / old_name
                    normalized_name = (
                        f"{fit_component(normalize_component(Path(old_name).stem), output_dir)}"
                        f"{Path(old_name).suffix.lower()}"
                    )
                    final_name = (
                        candidate.name
                        if candidate.is_file()
                        else normalized_name
                        if (output_dir / normalized_name).is_file()
                        else old_name
                    )
                    if final_name != old_name:
                        entry[key] = final_name
                        changed = True
                old_original = str(entry.get("original_transcription", ""))
                if old_original:
                    original_dir = output_dir / "original_transcriptions"
                    candidate = original_dir / old_original
                    normalized_name = (
                        f"{fit_component(normalize_component(Path(old_original).stem), original_dir)}"
                        f"{Path(old_original).suffix.lower()}"
                    )
                    final_name = (
                        candidate.name
                        if candidate.is_file()
                        else normalized_name
                        if (original_dir / normalized_name).is_file()
                        else old_original
                    )
                    if final_name != old_original:
                        entry["original_transcription"] = final_name
                        changed = True
                relative_output = entry.get("output_relative_path")
                if isinstance(relative_output, str):
                    output_name = str(entry.get("video", ""))
                    new_relative = f"{new_folder}/{output_name}" if output_name else relative_output
                    if new_relative != relative_output:
                        entry["output_relative_path"] = new_relative
                        changed = True
            if changed:
                try:
                    write_manifest(manifest, data.get("entries", []), metadata=data.get("metadata", {}))
                except OSError:
                    logger.warning("Could not update migrated manifest: %s", manifest)

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        source = Path(file.id).resolve()
        return {"sha256": sha256_file(source), "size": source.stat().st_size}

    def is_processed(self, file: StorageFile) -> bool:
        fingerprint = self.source_fingerprint(file)
        registry = ProcessedRegistry(self._storage_root("storage/state") / "processed.jsonl")
        return registry.contains_success(file.name, str(fingerprint["sha256"]))

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        if status != "success" or not self.retain_sources:
            return
        source = Path(file.id).resolve()
        if not source.is_file():
            logger.warning("Source already absent during finalization: %s", source)
            return
        try:
            fingerprint = self.source_fingerprint(file)
            archive_root = self._storage_root("storage/archive/sources")
            archive_root.mkdir(parents=True, exist_ok=True)
            short_hash = str(fingerprint["sha256"])[:16]
            archive_stem = fit_component(f"{source.stem}__{short_hash}", archive_root)
            archive_name = f"{archive_stem}{source.suffix.lower()}"
            archive_path = archive_root / archive_name
            shutil.copy2(source, archive_path)
        except FileNotFoundError:
            logger.warning("Source disappeared during finalization: %s", source)
            return
        archived_hash = sha256_file(archive_path)
        if archived_hash != fingerprint["sha256"]:
            archive_path.unlink(missing_ok=True)
            raise RuntimeError("Archived source hash mismatch")
        registry = ProcessedRegistry(self._storage_root("storage/state") / "processed.jsonl")
        registry.append_success(
            source_name=file.name,
            sha256=str(fingerprint["sha256"]),
            size=int(fingerprint["size"]),
            archive_name=archive_name,
            output_folders=output_folders or [],
        )
        source.unlink(missing_ok=True)
