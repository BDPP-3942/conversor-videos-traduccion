from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from config.loader import load_settings
from config.settings import BASE_DIR, AppSettings, resolve_project_path
from src.controllable_pipeline import ControllableMediaPipeline, PipelineCancelled
from src.output_deduplicator import OutputDeduplicator
from src.reprocessor import SubtitleReprocessor
from src.storage.factory import create_storage_provider

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[dict[str, object]], None]


class ApplicationError(RuntimeError):
    """User-facing application orchestration error."""


class VideoTranslationApplication:
    """Stable application/use-case facade shared by desktop and future clients."""

    _RUN_OPTIONS = {
        "source_lang",
        "target_lang",
        "translation_provider",
        "translation_fallback_providers",
        "whisper_model",
        "whisper_device",
        "whisper_compute_type",
        "whisper_beam_size",
        "whisper_vad_filter",
        "whisper_min_silence_duration_ms",
        "whisper_subtitle_split_silence_duration_ms",
        "whisper_condition_on_previous_text",
        "whisper_initial_prompt",
        "whisper_cpu_threads",
        "whisper_repetition_threshold",
        "whisper_compression_ratio_threshold",
        "whisper_log_prob_threshold",
        "whisper_no_speech_threshold",
        "whisper_min_repetition_words",
        "whisper_recovery_retries",
        "translation_batch_size",
        "translation_retries",
        "translation_max_retries_per_provider",
        "translation_max_parallel_requests",
        "local_translation_model",
        "local_translation_device",
        "local_translation_compute_type",
        "local_translation_beam_size",
        "max_zip_depth",
        "max_extracted_files",
        "max_extracted_size_gb",
        "ffmpeg_preset",
        "ffmpeg_crf",
        "ffmpeg_audio_bitrate",
        "generate_webm",
        "secondary_video_extension",
        "secondary_video_codec",
        "secondary_video_crf",
        "secondary_video_max_width",
        "secondary_video_fps",
        "secondary_video_audio_codec",
        "secondary_video_audio_bitrate",
        "ffmpeg_avoid_reencode",
        "tts_enabled",
        "tts_required",
        "tts_voice",
        "tts_speed",
        "tts_max_speed",
        "tts_duration_tolerance",
        "tts_audio_bitrate",
        "tts_webm_audio_bitrate",
        "resume_enabled",
        "normalize_legacy_names",
        "rename_processed_duplicates",
        "automatic_output_deduplication",
        "max_parallel_videos",
        "duplicate_name_similarity_threshold",
        "duplicate_duration_tolerance_seconds",
        "duplicate_visual_similarity_threshold",
    }

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (BASE_DIR / "config" / "app.toml")

    def load_settings(self) -> AppSettings:
        return load_settings(self.config_path)

    def _settings(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        provider: str | None = None,
        overrides: dict[str, object] | None = None,
    ) -> AppSettings:
        settings = self.load_settings()
        changes: dict[str, object] = {}
        if provider:
            changes["provider"] = provider
        if source:
            changes["source"] = self._as_local_uri(source)
        if target:
            changes["target"] = self._as_local_uri(target)
        if overrides:
            invalid = sorted(set(overrides) - self._RUN_OPTIONS)
            if invalid:
                raise ApplicationError(f"Unsupported application options: {', '.join(invalid)}")
            changes.update(overrides)
        return replace(settings, **changes)

    def run(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        provider: str | None = None,
        progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
        **overrides: object,
    ) -> dict[str, object]:
        settings = self._settings(
            source=source,
            target=target,
            provider=provider,
            overrides=overrides,
        )
        storage = create_storage_provider(settings.provider, settings)
        try:
            pipeline = ControllableMediaPipeline(
                settings,
                storage,
                event_callback=progress,
                cancel_event=cancel_event,
            )
            result = pipeline.run(settings.source, settings.target)
            self._emit(
                progress,
                "completed",
                100,
                result.get("zips_processed", 0),
                "Processing completed",
            )
            return result
        except PipelineCancelled as exc:
            self._emit(progress, "cancelled", 0, 0, str(exc))
            raise ApplicationError(str(exc)) from exc
        except Exception as exc:
            logger.exception("Desktop application run failed")
            self._emit(progress, "error", 0, 0, str(exc))
            raise ApplicationError(str(exc)) from exc
        finally:
            storage.close()

    def reprocess_subtitles(
        self,
        *,
        target: str,
        mode: str = "full",
        output_folder: str | None = None,
        video_name: str | None = None,
        source: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        settings = self._settings(target=target, provider=provider)
        storage = create_storage_provider(settings.provider, settings)
        try:
            return SubtitleReprocessor(settings, storage).reprocess(
                target if provider != "local" else settings.target,
                mode=mode,
                output_folder=output_folder,
                video_name=video_name,
                source=source,
            )
        finally:
            storage.close()

    def reprocess_all(
        self,
        *,
        target: str,
        mode: str = "full",
        provider: str | None = None,
    ) -> dict[str, Any]:
        settings = self._settings(target=target, provider=provider)
        storage = create_storage_provider(settings.provider, settings)
        try:
            return SubtitleReprocessor(settings, storage).reprocess_all(
                settings.target,
                mode=mode,
            )
        finally:
            storage.close()

    @staticmethod
    def deduplicate(target: str, action: str, *, dry_run: bool = False) -> dict[str, Any]:
        deduplicator = OutputDeduplicator(
            resolve_project_path(target.removeprefix("local://"))
        )
        if action == "scan":
            return deduplicator.scan_and_persist()
        if action == "analyze":
            return deduplicator.analyze_and_persist()
        if action == "delete":
            return {
                "results": deduplicator.delete(dry_run=dry_run),
                "dry_run": dry_run,
            }
        raise ApplicationError(f"Unsupported duplicate action: {action}")

    @staticmethod
    def _as_local_uri(value: str) -> str:
        path = Path(value).expanduser().resolve()
        return f"local://{path}"

    @staticmethod
    def _emit(
        callback: ProgressCallback | None,
        stage: str,
        percent: int,
        completed: int,
        message: str,
    ) -> None:
        if callback:
            callback(
                {
                    "stage": stage,
                    "percent": percent,
                    "completed": completed,
                    "message": message,
                }
            )
