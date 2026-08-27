from pathlib import Path

import pytest

from src import subtitle_qa
from src.subtitle_qa import SubtitleCue, validate_alignment, write_vtt


def test_validate_alignment_rejects_changed_timing() -> None:
    source = [SubtitleCue(1, "00:00:01.000", "00:00:02.000", "Hello")]
    target = [SubtitleCue(1, "00:00:01.100", "00:00:02.000", "Hello")]
    with pytest.raises(ValueError, match="timing/index changed"):
        validate_alignment(target, source)


def test_write_and_read_vtt_preserves_timing(tmp_path: Path) -> None:
    path = tmp_path / "sample.vtt"
    cues = [SubtitleCue(1, "00:00:01.000", "00:00:02.000", "Hello")]
    write_vtt(path, cues)
    assert subtitle_qa.read_vtt(path) == cues


def test_languagetool_can_report_and_apply_safe_suggestion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(_url: str, _payload: object, timeout: float = 60.0) -> object:
        assert timeout == 60.0
        return {
            "matches": [
                {
                    "offset": 0,
                    "length": 2,
                    "message": "Possible agreement error",
                    "rule": {"issueType": "grammar"},
                    "replacements": [{"value": "He"}],
                }
            ]
        }

    monkeypatch.setattr(subtitle_qa, "_post_json", fake_request)
    provider = subtitle_qa.LanguageToolProvider("http://localhost:8081/v2/check", "en-US")
    cues = [SubtitleCue(1, "00:00:01.000", "00:00:02.000", "Hi")]
    corrected, issues = provider.review(cues, auto_correct=True)
    assert issues[0].suggestion == "He"
    assert corrected[0].text == "He"
    assert corrected[0].start == cues[0].start
    assert corrected[0].end == cues[0].end


def test_ollama_reviewer_preserves_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(_url: str, payload: object, timeout: float = 60.0) -> object:
        assert timeout == 60.0
        assert isinstance(payload, dict)
        return {
            "message": {
                "content": '{"changed": true, "corrected_text": "We need to leave.", "issues": ["grammar"], "confidence": 0.98}'
            }
        }

    monkeypatch.setattr(subtitle_qa, "_post_json", fake_request)
    provider = subtitle_qa.OllamaProvider("http://localhost:11434/api/chat", "qwen3:8b")
    cues = [SubtitleCue(1, "00:00:01.000", "00:00:03.000", "We need leave.")]
    corrected, issues = provider.review(cues, source=[SubtitleCue(1, cues[0].start, cues[0].end, "We need to leave.")], auto_correct=True)
    assert corrected[0].text == "We need to leave."
    assert corrected[0].start == cues[0].start
    assert corrected[0].end == cues[0].end
    assert issues[0].confidence == 0.98
