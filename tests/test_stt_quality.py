from types import SimpleNamespace

from src.stt_quality import STTQualityThresholds, candidate_key, quality_metrics, suspicious_reasons


def segment(text: str, **metrics):
    return SimpleNamespace(text=text, **metrics)


def test_normal_long_text_is_not_suspicious():
    value = segment("Pong Yang, expansión y ondulación con cambio de peso y continuidad circular")
    reasons = suspicious_reasons(quality_metrics(value), STTQualityThresholds())
    assert reasons == ()


def test_short_legitimate_repetition_is_not_suspicious():
    value = segment("Pong, Pong, Pong")
    assert suspicious_reasons(quality_metrics(value), STTQualityThresholds()) == ()


def test_pathological_single_word_repetition_is_suspicious():
    value = segment("Pong " * 12)
    reasons = suspicious_reasons(quality_metrics(value), STTQualityThresholds())
    assert "repetition" in reasons


def test_pathological_other_word_is_suspicious():
    value = segment("Peng " * 12)
    assert "repetition" in suspicious_reasons(quality_metrics(value), STTQualityThresholds())


def test_repeated_ngram_is_suspicious():
    value = segment("the monkey sees " * 8)
    metrics = quality_metrics(value)
    assert metrics.repeated_trigram_ratio > 0.6
    assert "repetition" in suspicious_reasons(metrics, STTQualityThresholds())


def test_quality_metrics_tolerate_missing_optional_values():
    metrics = quality_metrics(segment("Texto normal"))
    assert metrics.compression_ratio is None
    assert metrics.avg_logprob is None
    assert metrics.no_speech_prob is None


def test_low_logprob_and_no_speech_are_combined():
    value = segment(
        "texto",
        avg_logprob=-1.5,
        no_speech_prob=0.8,
        compression_ratio=1.0,
    )
    reasons = suspicious_reasons(quality_metrics(value), STTQualityThresholds())
    assert "low_logprob" in reasons
    assert "no_speech" in reasons


def test_healthy_candidate_ranks_before_degenerate_candidate():
    healthy = segment("Pong Yang, expansión y ondulación", compression_ratio=1.2, avg_logprob=-0.2)
    bad = segment("Pong " * 12, compression_ratio=3.5, avg_logprob=-1.8)
    thresholds = STTQualityThresholds()
    assert candidate_key(healthy, thresholds) < candidate_key(bad, thresholds)
