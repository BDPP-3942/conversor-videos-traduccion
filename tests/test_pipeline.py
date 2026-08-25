from pathlib import Path
from types import SimpleNamespace

from config.settings import AppSettings
from src.pipeline import MediaPipeline
from src.storage.base import StorageFile
from src.translator import TextTranslator


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


class _FallbackStorage:
    def __init__(self) -> None:
        self.uploads = []

    def ensure_folder(self, parent, name):
        path = Path(parent) / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def upload_file(self, local_path, target_folder, mime_type):
        self.uploads.append((local_path, target_folder, mime_type))


class _CountingConverter:
    def __init__(self, output_path):
        self.output_path = output_path
        self.calls = 0

    def convert(self, source_path, stem, processed_dir):
        self.calls += 1
        mp4_path = processed_dir / f"{stem}.mp4"
        mp4_path.write_bytes(b"processed")
        return SimpleNamespace(mp4_path=mp4_path, secondary_video_path=None)


class _CountingSTT:
    def __init__(self):
        self.calls = 0

    def transcribe(self, mp4_path):
        self.calls += 1
        return [
            {"start": 0, "end": 1, "text": "uno"},
            {"start": 1, "end": 2, "text": "dos"},
        ]


class _AlwaysFailProvider:
    def __init__(self):
        self.calls = 0

    def translate_batch(self, texts):
        self.calls += 1
        raise RuntimeError("primary unavailable")

    def translate(self, text):
        raise RuntimeError("primary unavailable")


class _WorkingProvider:
    def __init__(self):
        self.calls = 0

    def translate_batch(self, texts):
        self.calls += 1
        return [f"EN:{text}" for text in texts]

    def translate(self, text):
        return f"EN:{text}"


def test_translation_fallback_reuses_existing_stt_and_media_artifacts(tmp_path):
    extract_root = tmp_path / "extracted"
    extract_root.mkdir()
    source = extract_root / "video.mp4"
    source.write_bytes(b"source")
    work_root = tmp_path / "work"
    work_root.mkdir()

    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("mymemory",),
        translation_max_retries_per_provider=2,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    first = _AlwaysFailProvider()
    second = _WorkingProvider()
    translator = TextTranslator(settings)
    translator._providers = {"google": first, "mymemory": second}
    translator._get_provider = lambda name: translator._providers[name]

    stt = _CountingSTT()
    converter = _CountingConverter(work_root)
    storage = _FallbackStorage()
    pipeline = MediaPipeline.__new__(MediaPipeline)
    pipeline.settings = settings
    pipeline.storage = storage
    pipeline.media_converter = converter
    pipeline._worker_components = lambda: (stt, translator)

    metadata = SimpleNamespace(
        course="1",
        lesson="1",
        course_name="Course",
        lesson_name="Lesson",
        description="Description",
        output_stem="01x01_Lesson",
        confidence=1.0,
        review_required=False,
        review_reason="",
    )

    result = pipeline._process_media(
        source,
        extract_root,
        work_root,
        str(tmp_path / "output"),
        "01x01_Lesson",
        "video",
        metadata,
    )

    assert result["status"] == "success"
    assert result["translation_failed_segments"] == 0
    assert converter.calls == 1
    assert stt.calls == 1
    assert first.calls == 2
    assert second.calls == 1
    assert len(storage.uploads) == 3
