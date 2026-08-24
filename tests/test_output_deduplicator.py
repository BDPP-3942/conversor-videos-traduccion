from pathlib import Path

from src.output_deduplicator import OutputDeduplicator


def _write_folder(root: Path, name: str, video: bytes, vtt: bytes) -> None:
    folder = root / name
    folder.mkdir()
    (folder / f"{name}.mp4").write_bytes(video)
    (folder / f"{name}_en.vtt").write_bytes(vtt)


def test_stable_name_wins_over_fragile_name(tmp_path: Path) -> None:
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")

    deduplicator = OutputDeduplicator(tmp_path)
    decisions = deduplicator.find_decisions()

    assert len(decisions) == 1
    assert decisions[0].canonical.name == "37x07_Bombeos"
    assert [item.name for item in decisions[0].duplicates] == ["wetransfer_Bombeos_20260728"]


def test_equal_stability_does_not_delete(tmp_path: Path) -> None:
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "37x07_Otro", b"video", b"vtt")

    deduplicator = OutputDeduplicator(tmp_path)

    assert deduplicator.find_decisions() == []


def test_delete_removes_only_fragile_duplicate(tmp_path: Path) -> None:
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")

    results = OutputDeduplicator(tmp_path, dry_run=False).apply()

    assert len(results) == 1
    assert (tmp_path / "37x07_Bombeos").is_dir()
    assert not (tmp_path / "wetransfer_Bombeos_20260728").exists()


def test_different_content_is_not_a_duplicate(tmp_path: Path) -> None:
    _write_folder(tmp_path, "37x07_Bombeos", b"video-a", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video-b", b"vtt")

    assert OutputDeduplicator(tmp_path).find_decisions() == []


def test_name_stability_score_prefers_canonical_structure() -> None:
    stable, _ = OutputDeduplicator.name_stability("37x07_Bombeos")
    fragile, _ = OutputDeduplicator.name_stability("SIN_CURSOxSIN_LECCION_wetransfer_Bombeos_20260728")
    assert stable > fragile


def test_dry_run_does_not_delete_fragile_duplicate(tmp_path: Path) -> None:
    _write_folder(tmp_path, "37x07_Bombeos", b"video", b"vtt")
    _write_folder(tmp_path, "wetransfer_Bombeos_20260728", b"video", b"vtt")

    results = OutputDeduplicator(tmp_path, dry_run=True).apply()

    assert results[0]["status"] == "planned"
    assert (tmp_path / "37x07_Bombeos").is_dir()
    assert (tmp_path / "wetransfer_Bombeos_20260728").is_dir()
