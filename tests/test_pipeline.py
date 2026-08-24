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
