from pathlib import Path

from src.application import VideoTranslationApplication


def test_application_facade_builds_local_uris_and_delegates(monkeypatch, tmp_path):
    captured = {}

    class Storage:
        def close(self):
            captured["closed"] = True

    class Pipeline:
        def __init__(self, settings, storage):
            captured["settings"] = settings
            captured["storage"] = storage

        def run(self, source, target):
            captured["source"] = source
            captured["target"] = target
            return {"status": "success", "zips_processed": 1}

    monkeypatch.setattr("src.application.create_storage_provider", lambda provider, settings: Storage())
    monkeypatch.setattr("src.application.MediaPipeline", Pipeline)
    app = VideoTranslationApplication()
    result = app.run(source=str(tmp_path / "input"), target=str(tmp_path / "output"), max_parallel_videos=1)

    assert result["status"] == "success"
    assert captured["source"] == f"local://{Path(tmp_path / 'input').resolve()}"
    assert captured["target"] == f"local://{Path(tmp_path / 'output').resolve()}"
    assert captured["settings"].max_parallel_videos == 1
    assert captured["closed"] is True
