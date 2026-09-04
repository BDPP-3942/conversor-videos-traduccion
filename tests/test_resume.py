from pathlib import Path

from src.manifest import read_manifest, write_manifest
from src.pipeline import MediaPipeline


class _ResumeStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.processed_calls = 0

    def normalize_existing_output_names(self, target, original_transcript_subdir):
        return {}

    def list_zip_files(self, source):
        return []

    def is_processed(self, file):
        return False

    def ensure_folder(self, parent, name):
        folder = Path(parent) / name
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)

    def folder_exists(self, parent, name):
        return (Path(parent) / name).is_dir()

    def file_exists(self, parent, name):
        return (Path(parent) / name).is_file()


def _build_resume_storage(tmp_path):
    storage = _ResumeStorage(tmp_path / "output")
    folder = storage.ensure_folder(str(storage.root), "37x02_tema")
    original = storage.ensure_folder(folder, "original_transcriptions")
    (Path(folder) / "37x02_tema.mp4").write_bytes(b"mp4")
    (Path(folder) / "37x02_tema.mp3").write_bytes(b"mp3")
    (Path(folder) / "37x02_tema_en.vtt").write_text("WEBVTT\n", encoding="utf-8")
    (Path(original) / "37x02_tema_original.vtt").write_text("WEBVTT\n", encoding="utf-8")
    return storage


def test_resume_entry_is_reused_when_all_artifacts_exist(tmp_path):
    storage = _build_resume_storage(tmp_path)
    pipeline = MediaPipeline.__new__(MediaPipeline)
    pipeline.storage = storage
    pipeline.settings = type(
        "Settings",
        (),
        {"original_transcript_subdir": "original_transcriptions", "target_lang": "en"},
    )()

    resumed = pipeline._try_resume(
        {
            "source": "curso 37/02 - Tema.mp4",
            "status": "success",
            "output_folder": "37x02_tema",
            "video": "37x02_tema.mp4",
            "audio": "37x02_tema.mp3",
            "translated_vtt": "37x02_tema_en.vtt",
            "original_transcription": "37x02_tema_original.vtt",
        },
        str(storage.root),
        "curso 37/02 - Tema.mp4",
    )

    assert resumed is not None
    assert resumed["output_folder"] == "37x02_tema"
    assert resumed["video"] == "37x02_tema.mp4"


def test_manifest_supports_legacy_list_and_new_metadata(tmp_path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text('[{"source":"video.mp4","status":"success"}]', encoding="utf-8")
    data = read_manifest(legacy)
    assert data["version"] == 1
    assert data["entries"][0]["source"] == "video.mp4"

    current = tmp_path / "current.json"
    write_manifest(current, [{"source": "video.mp4", "status": "success"}], metadata={"zip_name": "x.zip"})
    data = read_manifest(current)
    assert data["version"] == 2
    assert data["metadata"]["zip_name"] == "x.zip"
