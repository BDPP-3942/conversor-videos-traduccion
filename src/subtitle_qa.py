from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import webvtt


@dataclass(frozen=True)
class SubtitleCue:
    index: int
    start: str
    end: str
    text: str


@dataclass(frozen=True)
class QAIssue:
    engine: str
    cue_index: int
    issue_type: str
    message: str
    original_text: str
    suggestion: str = ""
    confidence: float = 0.0


class SubtitleQAError(RuntimeError):
    pass


def read_vtt(path: Path) -> list[SubtitleCue]:
    captions = webvtt.read(str(path))
    cues = [SubtitleCue(i, c.start, c.end, c.text.strip()) for i, c in enumerate(captions, 1)]
    if not cues:
        raise ValueError(f"VTT contains no cues: {path}")
    return cues


def write_vtt(path: Path, cues: list[SubtitleCue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("WEBVTT\n\n")
        for cue in cues:
            handle.write(f"{cue.start} --> {cue.end}\n{cue.text}\n\n")


def validate_alignment(cues: list[SubtitleCue], source: list[SubtitleCue] | None = None) -> None:
    if not cues:
        raise ValueError("No subtitle cues supplied")
    if source is None:
        return
    if len(source) != len(cues):
        raise ValueError(f"Source/target cue count mismatch: {len(source)} != {len(cues)}")
    for src, dst in zip(source, cues, strict=True):
        if src.index != dst.index or src.start != dst.start or src.end != dst.end:
            raise ValueError(f"Subtitle timing/index changed at cue {dst.index}")


def _post_json(url: str, payload: object, timeout: float = 60.0) -> object:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("QA service URL must use HTTP or HTTPS")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SubtitleQAError(f"QA service HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SubtitleQAError(f"QA service connection failed: {exc}") from exc


def _post_form(url: str, payload: dict[str, str], timeout: float = 60.0) -> object:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("QA service URL must use HTTP or HTTPS")
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SubtitleQAError(f"QA service HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SubtitleQAError(f"QA service connection failed: {exc}") from exc


class LanguageToolProvider:
    name = "languagetool"

    def __init__(self, url: str, language: str) -> None:
        self.url = url
        self.language = language

    @staticmethod
    def _apply(text: str, matches: list[dict[str, Any]]) -> str:
        replacements: list[tuple[int, int, str]] = []
        for match in matches:
            try:
                offset = int(match["offset"])
                length = int(match["length"])
                values = match.get("replacements", [])
                replacement = str(values[0].get("value", "")) if values else ""
            except (KeyError, TypeError, ValueError, IndexError):
                continue
            if replacement and 0 <= offset <= offset + length <= len(text):
                replacements.append((offset, length, replacement))
        replacements.sort(key=lambda item: item[0], reverse=True)
        last = len(text) + 1
        for offset, length, replacement in replacements:
            if offset + length > last:
                continue
            text = text[:offset] + replacement + text[offset + length :]
            last = offset
        return text

    def review(self, cues: list[SubtitleCue], *, auto_correct: bool) -> tuple[list[SubtitleCue], list[QAIssue]]:
        result_cues = list(cues)
        issues: list[QAIssue] = []
        for cue in cues:
            if not cue.text:
                continue
            result = _post_form(
                self.url,
                {"text": cue.text, "language": self.language, "enabledOnly": "false", "level": "picky"},
            )
            matches = result.get("matches", []) if isinstance(result, dict) else []
            if not isinstance(matches, list):
                raise SubtitleQAError("LanguageTool returned an invalid matches array")
            for match in matches:
                if not isinstance(match, dict):
                    continue
                values = match.get("replacements", [])
                suggestion = str(values[0].get("value", "")) if values and isinstance(values[0], dict) else ""
                rule = match.get("rule", {})
                issues.append(
                    QAIssue(
                        self.name,
                        cue.index,
                        str(rule.get("issueType", "unknown")),
                        str(match.get("message", "")),
                        cue.text,
                        suggestion,
                        1.0 if suggestion else 0.0,
                    )
                )
            if auto_correct and matches:
                result_cues[cue.index - 1] = SubtitleCue(
                    cue.index, cue.start, cue.end, self._apply(cue.text, [m for m in matches if isinstance(m, dict)])
                )
        return result_cues, issues


class OllamaProvider:
    name = "ollama"

    def __init__(self, url: str, model: str) -> None:
        self.url = url
        self.model = model

    def review(
        self,
        cues: list[SubtitleCue],
        *,
        source: list[SubtitleCue] | None,
        auto_correct: bool,
    ) -> tuple[list[SubtitleCue], list[QAIssue]]:
        result_cues = list(cues)
        source_by_index = {cue.index: cue.text for cue in source or []}
        issues: list[QAIssue] = []
        for pos, cue in enumerate(cues):
            payload = {
                "model": self.model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a meticulous English subtitle QA editor. Preserve meaning. Never alter timing, "
                            "merge/split cues, invent facts or dialogue. Return JSON only with changed, corrected_text, "
                            "issues, confidence."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "source": source_by_index.get(cue.index, ""),
                                "translated": cue.text,
                                "previous": cues[pos - 1].text if pos else "",
                                "next": cues[pos + 1].text if pos + 1 < len(cues) else "",
                                "task": (
                                    "Check spelling, grammar, punctuation, natural English, contextual meaning, "
                                    "inappropriate wording and terminology. Correct only when justified."
                                ),
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            }
            response = _post_json(self.url, payload)
            try:
                content = response["message"]["content"]
                parsed = json.loads(content) if isinstance(content, str) else content
                changed = bool(parsed["changed"])
                corrected = str(parsed["corrected_text"])
                confidence = max(0.0, min(1.0, float(parsed["confidence"])))
                issue_text = "; ".join(str(x) for x in parsed.get("issues", []))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise SubtitleQAError(f"Ollama returned invalid QA JSON for cue {cue.index}") from exc
            if changed and corrected.strip() and corrected != cue.text:
                issues.append(
                    QAIssue(
                        self.name,
                        cue.index,
                        "contextual",
                        issue_text or "LLM correction",
                        cue.text,
                        corrected,
                        confidence,
                    )
                )
                if auto_correct:
                    result_cues[cue.index - 1] = SubtitleCue(cue.index, cue.start, cue.end, corrected)
        return result_cues, issues


def run_subtitle_qa(
    vtt_path: Path,
    *,
    engine: str,
    source_vtt: Path | None = None,
    output_path: Path | None = None,
    report_path: Path | None = None,
    auto_correct: bool = False,
    languagetool_url: str = "http://127.0.0.1:8081/v2/check",
    languagetool_language: str = "en-US",
    ollama_url: str = "http://127.0.0.1:11434/api/chat",
    ollama_model: str = "qwen3:8b",
) -> dict[str, Any]:
    original = read_vtt(vtt_path)
    source = read_vtt(source_vtt) if source_vtt else None
    validate_alignment(original, source)
    selected = engine.lower().replace("-", "_")
    providers: list[Any] = []
    if selected in {"languagetool", "language_tool", "both"}:
        providers.append(LanguageToolProvider(languagetool_url, languagetool_language))
    if selected in {"llm", "ollama", "both"}:
        providers.append(OllamaProvider(ollama_url, ollama_model))
    if not providers:
        raise ValueError(f"Unsupported subtitle QA engine: {engine}")
    current = original
    all_issues: list[QAIssue] = []
    provider_results = []
    for provider in providers:
        if isinstance(provider, LanguageToolProvider):
            current, issues = provider.review(current, auto_correct=auto_correct)
        else:
            current, issues = provider.review(current, source=source, auto_correct=auto_correct)
        validate_alignment(current, source)
        all_issues.extend(issues)
        provider_results.append({"engine": provider.name, "issues": len(issues)})
    changed = current != original
    if changed and auto_correct and output_path:
        write_vtt(output_path, current)
    report = {
        "status": "changes" if changed else "clean",
        "engine": selected,
        "input_vtt": str(vtt_path),
        "source_vtt": str(source_vtt) if source_vtt else None,
        "output_vtt": str(output_path) if changed and auto_correct and output_path else None,
        "auto_correct": auto_correct,
        "cues": len(original),
        "issues": len(all_issues),
        "providers": provider_results,
        "changes": [issue.__dict__ for issue in all_issues],
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
