from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_WORD_RE = re.compile(r"\b[\w’'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class STTQualityMetrics:
    word_count: int
    unique_ratio: float
    dominant_word_ratio: float
    repeated_bigram_ratio: float
    repeated_trigram_ratio: float
    repetition_score: float
    compression_ratio: float | None
    avg_logprob: float | None
    no_speech_prob: float | None


@dataclass(frozen=True)
class STTQualityThresholds:
    repetition_threshold: float = 0.60
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    min_repetition_words: int = 8


def _ratio_repeated_ngrams(words: list[str], size: int) -> float:
    if len(words) < size:
        return 0.0
    ngrams = [tuple(words[i : i + size]) for i in range(len(words) - size + 1)]
    counts: dict[tuple[str, ...], int] = {}
    for ngram in ngrams:
        counts[ngram] = counts.get(ngram, 0) + 1
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(ngrams)


def measure_repetition(text: str) -> tuple[float, float, float, float, float]:
    words = [match.group(0).casefold() for match in _WORD_RE.finditer(text)]
    if not words:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    frequencies: dict[str, int] = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1

    unique_ratio = len(frequencies) / len(words)
    dominant_word_ratio = max(frequencies.values()) / len(words)
    repeated_bigram_ratio = _ratio_repeated_ngrams(words, 2)
    repeated_trigram_ratio = _ratio_repeated_ngrams(words, 3)
    repetition_score = max(
        dominant_word_ratio,
        repeated_bigram_ratio,
        repeated_trigram_ratio,
    )
    return (
        unique_ratio,
        dominant_word_ratio,
        repeated_bigram_ratio,
        repeated_trigram_ratio,
        repetition_score,
    )


def quality_metrics(segment: Any) -> STTQualityMetrics:
    text = str(getattr(segment, "text", "") or "").strip()
    words = _WORD_RE.findall(text)
    unique_ratio, dominant, bigram, trigram, repetition = measure_repetition(text)

    def optional_float(name: str) -> float | None:
        value = getattr(segment, name, None)
        return float(value) if value is not None else None

    return STTQualityMetrics(
        word_count=len(words),
        unique_ratio=unique_ratio,
        dominant_word_ratio=dominant,
        repeated_bigram_ratio=bigram,
        repeated_trigram_ratio=trigram,
        repetition_score=repetition,
        compression_ratio=optional_float("compression_ratio"),
        avg_logprob=optional_float("avg_logprob"),
        no_speech_prob=optional_float("no_speech_prob"),
    )


def suspicious_reasons(
    metrics: STTQualityMetrics,
    thresholds: STTQualityThresholds,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        metrics.word_count >= thresholds.min_repetition_words
        and metrics.repetition_score >= thresholds.repetition_threshold
    ):
        reasons.append("repetition")

    if (
        metrics.compression_ratio is not None
        and metrics.compression_ratio > thresholds.compression_ratio_threshold
    ):
        reasons.append("compression")

    low_probability = (
        metrics.avg_logprob is not None
        and metrics.avg_logprob < thresholds.log_prob_threshold
    )
    high_no_speech = (
        metrics.no_speech_prob is not None
        and metrics.no_speech_prob > thresholds.no_speech_threshold
    )
    if low_probability:
        reasons.append("low_logprob")
    if high_no_speech and low_probability:
        reasons.append("no_speech")

    return tuple(reasons)


def candidate_key(
    segment: Any,
    thresholds: STTQualityThresholds,
) -> tuple[bool, float, float, float, float, float]:
    metrics = quality_metrics(segment)
    reasons = suspicious_reasons(metrics, thresholds)
    compression_excess = max(
        0.0,
        (metrics.compression_ratio or 0.0) - thresholds.compression_ratio_threshold,
    )
    logprob_deficit = max(
        0.0,
        thresholds.log_prob_threshold - (metrics.avg_logprob or thresholds.log_prob_threshold),
    )
    no_speech_excess = max(
        0.0,
        (metrics.no_speech_prob or 0.0) - thresholds.no_speech_threshold,
    )
    return (
        bool(reasons),
        metrics.repetition_score,
        compression_excess,
        logprob_deficit,
        no_speech_excess,
        -metrics.unique_ratio,
    )
