from pathlib import Path

import pytest

from src.translation_quota import TranslationQuotaExceeded, TranslationQuotaGuard


def test_quota_guard_reserves_and_blocks_over_limit(tmp_path: Path):
    guard = TranslationQuotaGuard(tmp_path / "quota.json")
    guard._window = lambda provider, now: ("test", 5)
    assert guard.reserve("deepl", ["abc"]) == 3
    with pytest.raises(TranslationQuotaExceeded):
        guard.reserve("deepl", ["def"])
