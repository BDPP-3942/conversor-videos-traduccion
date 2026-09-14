from pathlib import Path
import threading

from src.application import ApplicationError, VideoTranslationApplication


def test_application_facade_builds_local_uris_and_delegates(monkeypatch, tmp_path):
    captured = {}

    class Storage:
        def close(self):
            captured["closed"] = True

    class Pipeline:
        def __init__(self, settings, storage, **kwargs):
            captured["settings"] = settings
            captured["storage"] = storage
            captured["callback"] = kwargs["event_callback"]
            captured["cancel_event"] = kwargs["cancel_event"]

        def run(self, source, target):
            captured["source"] = source
            captured["target"] = target
            return {"status": "success", "zips_processed": 1}

    monkeypatch.setattr("src.application.create_storage_provider", lambda provider, settings: Storage())
    monkeypatch.setattr("src.application.ControllableMediaPipeline", Pipeline)
    app = VideoTranslationApplication()
    events = []
    cancel_event = threading.Event()
    result = app.run(
        source=str(tmp_path / "input"),
        target=str(tmp_path / "output"),
        progress=events.append,
        cancel_event=cancel_event,
        max_parallel_videos=1,
    )

    assert result["status"] == "success"
    assert captured["source"] == f"local://{Path(tmp_path / 'input').resolve()}"
    assert captured["target"] == f"local://{Path(tmp_path / 'output').resolve()}"
    assert captured["settings"].max_parallel_videos == 1
    assert captured["callback"] is events.append
    assert captured["cancel_event"] is cancel_event
    assert captured["closed"] is True
    assert events[-1]["stage"] == "completed"


def test_application_rejects_unknown_run_options(tmp_path):
    app = VideoTranslationApplication()
    try:
        app.run(source=str(tmp_path), target=str(tmp_path), unknown_option=True)
    except ApplicationError as exc:
        assert "unknown_option" in str(exc)
    else:
        raise AssertionError("ApplicationError was not raised")
