from types import SimpleNamespace

from src.pipeline import MediaPipeline
from src.storage.base import StorageFile


class _Storage:
    def __init__(self) -> None:
        self.finalize_calls = 0

    def list_zip_files(self, source: str) -> list[StorageFile]:
        return [StorageFile(id="input.zip", name="input.zip")]

    def is_processed(self, file: StorageFile) -> bool:
        return False

    def finalize_source(self, file: StorageFile, status: str, output_folders=None) -> None:
        self.finalize_calls += 1
        raise FileNotFoundError("source disappeared before archive cleanup")


def test_pipeline_does_not_turn_finalize_filenotfound_into_zip_failure():
    pipeline = MediaPipeline.__new__(MediaPipeline)
    pipeline.storage = _Storage()
    pipeline._process_zip = lambda zip_file, target: {
        "zip": zip_file.name,
        "status": "success",
        "output_folders": [],
    }

    result = pipeline.run("input", "output")

    assert result["status"] == "success"
    assert result["zips_failed"] == 0
    assert result["zips"][0]["status"] == "success"
    assert pipeline.storage.finalize_calls == 1


class _DuplicateIdentity:
    def candidate_names(self, registry, normalized_name):
        return [entry for entry in registry if entry.get("normalized_name") == normalized_name]

    def find_duplicate(self, source_path, normalized_name, candidates):
        assert source_path.is_file()
        assert normalized_name == "7 opt taich bombeos"
        return SimpleNamespace(
            status="duplicate_exact",
            score=1.0,
            reason="test",
            registry_entry=candidates[0],
        )


def test_pipeline_duplicate_lookup_uses_resolver_instance(tmp_path):
    source = tmp_path / "7 opt taich bombeos.mp4"
    source.write_bytes(b"video")

    pipeline = MediaPipeline.__new__(MediaPipeline)
    pipeline.media_identity = _DuplicateIdentity()

    registry = [
        {
            "status": "success",
            "source": "first.zip/video.mp4",
            "output_folder": "37x07_Bombeos",
            "normalized_name": "7 opt taich bombeos",
            "sha256": "different",
        }
    ]

    match = pipeline._find_media_duplicate(source, "7 opt taich bombeos", registry)

    assert match is not None
    assert match["status"] == "duplicate_exact"
    assert match["registry_entry"]["output_folder"] == "37x07_Bombeos"
