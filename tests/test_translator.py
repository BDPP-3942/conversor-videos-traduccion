from config.settings import AppSettings
from src.translator import TextTranslator


class FakeTranslator:
    calls = 0

    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target

    def translate_batch(self, texts):
        FakeTranslator.calls += 1
        if FakeTranslator.calls == 1:
            raise RuntimeError("temporary provider error")
        return [f"EN:{text}" for text in texts]

    def translate(self, text):
        return f"EN:{text}"


def test_batch_translation_recovers_without_raising():
    settings = AppSettings(
        translation_retries=1,
        translation_batch_size=4,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    translator = TextTranslator.__new__(TextTranslator)
    translator.settings = settings
    translator._last_request_at = 0.0
    translator._failed_segments = 0
    translator._translator_factory = FakeTranslator
    translator.translator = FakeTranslator("es", "en")

    result = translator.translate_segments(
        [{"start": 0, "end": 1, "text": "uno"}, {"start": 1, "end": 2, "text": "dos"}]
    )

    assert [item["text"] for item in result] == ["EN:uno", "EN:dos"]
    assert all("translation_failed" not in item for item in result)


class AlwaysFailTranslator(FakeTranslator):
    def translate_batch(self, texts):
        raise RuntimeError("provider unavailable")

    def translate(self, text):
        raise RuntimeError("provider unavailable")


def test_final_translation_failure_preserves_source_and_marks_segment(monkeypatch):
    settings = AppSettings(
        translation_retries=1,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    translator = TextTranslator.__new__(TextTranslator)
    translator.settings = settings
    translator._last_request_at = 0.0
    translator._failed_segments = 0
    translator._translator_factory = AlwaysFailTranslator
    translator.translator = AlwaysFailTranslator("es", "en")

    result = translator.translate_segments([{"start": 0, "end": 1, "text": "uno"}])

    assert result[0]["text"] == "uno"
    assert result[0]["translation_failed"] is True
