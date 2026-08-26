import json
from pathlib import Path

from src.output_deduplicator import OutputDeduplicator


def _write_folder(root: Path, name: str, video: bytes, vtt: bytes) -> None:
    folder = root / name
    folder.mkdir()
    (folder / f"{name}.mp4").write_bytes(video)
    (folder / f"{name}_en.vtt").write_bytes(vtt)


def test_scan_finds_duplicates_without_modifying_results(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    before = sorted((p.name, p.stat().st_mtime_ns) for p in tmp_path.rglob("*"))
    folders = OutputDeduplicator(tmp_path).scan()
    after = sorted((p.name, p.stat().st_mtime_ns) for p in tmp_path.rglob("*"))
    assert {folder.name for folder in folders} == {"37x07_Bombeos", "wetransfer_Bombeos_20260728"}
    assert before == after


def test_analyze_with_clear_referente(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    decisions = OutputDeduplicator(tmp_path).analyze(OutputDeduplicator(tmp_path).scan())
    assert len(decisions) == 1
    assert decisions[0].decision == "delete_duplicates"
    assert decisions[0].canonical.name == "37x07_Bombeos"
    assert decisions[0].duplicates[0].name == "wetransfer_Bombeos_20260728"


def test_analyze_without_clear_referente_never_marks_delete(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "37x07_Otro", b"video", b"vtt")
    decisions = OutputDeduplicator(tmp_path).analyze(OutputDeduplicator(tmp_path).scan())
    assert len(decisions) == 1
    assert decisions[0].decision == "keep"


def test_analyze_persists_reviewable_plan_without_deleting(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    plan = dedup.analyze_and_persist()
    assert plan["deletions"][0]["canonical"] == "37x07_Bombeos"
    assert plan["deletions"][0]["duplicate"] == "wetransfer_Bombeos_20260728"
    assert (tmp_path / "37x07_Bombeos").is_dir()
    assert (tmp_path / "wetransfer_Bombeos_20260728").is_dir()


def test_delete_dry_run_does_not_modify_anything(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    dedup.analyze_and_persist()
    before = sorted((p.name, p.stat().st_mtime_ns) for p in tmp_path.rglob("*"))
    results = dedup.delete(dry_run=True)
    after = sorted((p.name, p.stat().st_mtime_ns) for p in tmp_path.rglob("*"))
    assert results[0]["status"] == "planned"
    assert before == after
    assert (tmp_path / "wetransfer_Bombeos_20260728").is_dir()


def test_delete_removes_only_duplicate(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    dedup.analyze_and_persist()
    results = dedup.delete()
    assert results[0]["status"] == "deleted"
    assert (tmp_path / "37x07_Bombeos").is_dir()
    assert not (tmp_path / "wetransfer_Bombeos_20260728").exists()


def test_delete_never_deletes_referente(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    dedup.analyze_and_persist()
    dedup.delete()
    assert (tmp_path / "37x07_Bombeos").exists()


def test_unique_content_is_never_deleted(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video-a", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video-b", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    plan = dedup.analyze_and_persist()
    assert plan["deletions"] == []
    assert dedup.delete() == []
    assert (tmp_path / "37x07_Bombeos").exists()
    assert (tmp_path / "wetransfer_Bombeos_20260728").exists()


def test_delete_skips_when_duplicate_content_changed_after_analysis(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    dedup = OutputDeduplicator(tmp_path)
    dedup.scan_and_persist()
    dedup.analyze_and_persist()
    (tmp_path / "wetransfer_Bombeos_20260728" / "wetransfer_Bombeos_20260728.mp4").write_bytes(b"changed")
    results = dedup.delete()
    assert results[0]["status"] == "skipped"
    assert (tmp_path / "wetransfer_Bombeos_20260728").exists()


def test_delete_keeps_registry_and_manifests_consistent(tmp_path: Path):
    output = tmp_path / "output"
    output.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    manifests = output / "_manifests"
    manifests.mkdir()
    _write_folder(output, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(output, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    registry = state / "media_registry.jsonl"
    registry.write_text(
        json.dumps({"output_folder": "37x07_Bombeos", "source": "stable.zip/video.mp4"})
        + "\n"
        + json.dumps({"output_folder": "wetransfer_Bombeos_20260728", "source": "fragile.zip/video.mp4"})
        + "\n",
        encoding="utf-8",
    )
    manifest = manifests / "input.json"
    manifest.write_text(
        json.dumps(
            {
                "metadata": {},
                "entries": [
                    {"output_folder": "37x07_Bombeos", "source": "stable.zip/video.mp4"},
                    {"output_folder": "wetransfer_Bombeos_20260728", "source": "fragile.zip/video.mp4"},
                ],
            }
        ),
        encoding="utf-8",
    )
    dedup = OutputDeduplicator(output)
    dedup.scan_and_persist()
    dedup.analyze_and_persist()
    dedup.delete()
    assert "wetransfer_Bombeos_20260728" not in registry.read_text(encoding="utf-8")
    assert "37x07_Bombeos" in registry.read_text(encoding="utf-8")
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert [entry["output_folder"] for entry in manifest_data["entries"]] == ["37x07_Bombeos"]
    assert (state / "dedupe_history.jsonl").is_file()


def test_backward_compatible_apply_still_performs_automatic_cleanup(tmp_path: Path):
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")
    results = OutputDeduplicator(tmp_path).apply()
    assert results[0]["status"] == "deleted"
    assert (tmp_path / "37x07_Bombeos").exists()
    assert not (tmp_path / "wetransfer_Bombeos_20260728").exists()
