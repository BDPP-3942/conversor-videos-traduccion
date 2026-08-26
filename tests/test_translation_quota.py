from __future__ import annotations

from pathlib import Path

import pytest

from src.translation_quota import TranslationQuotaExceeded, TranslationQuotaGuard


def test_deepl_quota_is_reserved_by_character(tmp_path: Path):
    guard = TranslationQuotaGuard(tmp_path / "quotas.json")

    assert guard.reserve("deepl", ["hola", "mundo"]) == 9
    usage = guard.usage("deepl")

    assert usage is not None
    assert usage["used"] == 9
    assert usage["limit"] == 500_000
    assert usage["unit"] == "characters"


def test_mymemory_anonymous_quota_is_reserved_by_request(tmp_path: Path):
    guard = TranslationQuotaGuard(tmp_path / "quotas.json")

    assert guard.reserve("mymemory", ["uno", "dos", "tres"]) == 3
    usage = guard.usage("mymemory")

    assert usage is not None
    assert usage["used"] == 3
    assert usage["limit"] == 100
    assert usage["unit"] == "requests"


def test_mymemory_registered_quota_uses_email_allowance(tmp_path: Path):
    guard = TranslationQuotaGuard(tmp_path / "quotas.json", mymemory_registered=True)

    usage = guard.usage("mymemory")

    assert usage is not None
    assert usage["limit"] == 1_000


def test_quota_reservation_rejects_over_limit(tmp_path: Path):
    guard = TranslationQuotaGuard(tmp_path / "quotas.json")
    guard.reserve("mymemory", ["x"] * 100)

    with pytest.raises(TranslationQuotaExceeded):
        guard.reserve("mymemory", ["x"])
