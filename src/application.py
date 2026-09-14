from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Callable

from config.loader import load_settings
from config.settings import AppSettings, BASE_DIR
from src.pipeline import MediaPipeline
from src.storage.factory import create_storage_provider

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[dict[str, object]], None]


class ApplicationError(RuntimeError):
    """User-facing application orchestration error."""


class VideoTranslationApplication:
    """Stable application/use-case facade shared by desktop and future clients."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (BASE_DIR / "config" / "app.toml")

    def load_settings(self) -> AppSettings:
        return load_settings(self.config_path)

    def run(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        provider: str | None = None,
        progress: ProgressCallback | None = None,
        **overrides: object,
    ) -> dict[str, object]:
        settings = self.load_settings()
        if provider:
            settings = replace(settings, provider=provider)
        if source:
            settings = replace(settings, source=self._as_local_uri(source))
        if target:
            settings = replace(settings, target=self._as_local_uri(target))
        allowed = {
            "source_lang", "target_lang", "translation_provider", "translation_fallback_providers",
            "whisper_model", "whisper_device", "whisper_compute_type", "whisper_beam_size",
            "whisper_vad_filter", "whisper_initial_prompt", "whisper_recovery_retries",
            "translation_batch_size", "max_parallel_videos", "generate_webm", "tts_enabled",
            "tts_required", "tts_voice", "resume_enabled", "normalize_legacy_names",
        }
        invalid = sorted(set(overrides) - allowed)
        if invalid:
            raise ApplicationError(f"Unsupported application options: {', '.join(invalid)}")
        settings = replace(settings, **overrides)
        storage = create_storage_provider(settings.provider, settings)
        try:
            self._emit(progress, "preparing", 0, 0, "Preparing pipeline")
            pipeline = MediaPipeline(settings, storage)
            result = pipeline.run(settings.source, settings.target)
            self._emit(progress, "completed", 100, result.get("zips_processed", 0), "Processing completed")
            return result
        except Exception as exc:
            logger.exception("Desktop application run failed")
            self._emit(progress, "error", 0, 0, str(exc))
            raise ApplicationError(str(exc)) from exc
        finally:
            storage.close()

    @staticmethod
    def _as_local_uri(value: str) -> str:
        path = Path(value).expanduser().resolve()
        return f"local://{path}"

    @staticmethod
    def _emit(callback: ProgressCallback | None, stage: str, percent: int, completed: int, message: str) -> None:
        if callback:
            callback({"stage": stage, "percent": percent, "completed": completed, "message": message})
