from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.pipeline import MediaPipeline


PipelineEventCallback = Callable[[dict[str, object]], None]


class PipelineCancelled(BaseException):
    """Control-flow signal for cooperative cancellation at safe stage boundaries."""


class _StageConverter:
    def __init__(self, owner: ControllableMediaPipeline, wrapped: Any) -> None:
        self.owner = owner
        self.wrapped = wrapped

    def convert(self, *args: Any, **kwargs: Any) -> Any:
        source = args[0] if args else kwargs.get("source_path")
        name = getattr(source, "name", str(source))
        self.owner._check_cancelled()
        self.owner._emit("converting", f"Converting {name}", file=name, percent=10)
        result = self.wrapped.convert(*args, **kwargs)
        self.owner._check_cancelled()
        return result


class _StageSTT:
    def __init__(self, owner: ControllableMediaPipeline, wrapped: Any) -> None:
        self.owner = owner
        self.wrapped = wrapped

    def transcribe(self, *args: Any, **kwargs: Any) -> Any:
        source = args[0] if args else kwargs.get("audio_path")
        name = getattr(source, "name", str(source))
        self.owner._check_cancelled()
        self.owner._emit("transcribing", f"Transcribing {name}", file=name, percent=35)
        result = self.wrapped.transcribe(*args, **kwargs)
        self.owner._check_cancelled()
        return result


class _StageTranslator:
    def __init__(self, owner: ControllableMediaPipeline, wrapped: Any) -> None:
        self.owner = owner
        self.wrapped = wrapped

    def translate_segments(self, *args: Any, **kwargs: Any) -> Any:
        self.owner._check_cancelled()
        self.owner._emit("translating", "Translating subtitle segments", percent=65)
        result = self.wrapped.translate_segments(*args, **kwargs)
        self.owner._check_cancelled()
        return result


class ControllableMediaPipeline(MediaPipeline):
    """MediaPipeline adapter exposing stage progress and cooperative cancellation."""

    def __init__(
        self,
        settings,
        storage,
        *,
        event_callback: PipelineEventCallback | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        super().__init__(settings, storage)
        self.event_callback = event_callback
        self.cancel_event = cancel_event or threading.Event()
        self._completed_media = 0
        self._total_media_hint = 0
        self.media_converter = _StageConverter(self, self.media_converter)

    def _emit(self, stage: str, message: str, **details: object) -> None:
        if self.event_callback is None:
            return
        payload: dict[str, object] = {
            "stage": stage,
            "message": message,
            "completed": self._completed_media,
            "total": self._total_media_hint,
        }
        payload.update(details)
        self.event_callback(payload)

    def _check_cancelled(self) -> None:
        if self.cancel_event.is_set():
            self._emit("cancelled", "Cancellation requested; stopping at a safe stage boundary")
            raise PipelineCancelled("Processing cancelled by the user")

    def _worker_components(self):
        stt_engine, translator = super()._worker_components()
        if not isinstance(stt_engine, _StageSTT):
            stt_engine = _StageSTT(self, stt_engine)
            self._thread_local.stt_engine = stt_engine
        if not isinstance(translator, _StageTranslator):
            translator = _StageTranslator(self, translator)
            self._thread_local.translator = translator
        return stt_engine, translator

    def run(
        self,
        source: str,
        target: str,
        *,
        force_reprocess: bool = False,
        finalize_source: bool = True,
    ) -> dict[str, Any]:
        self._completed_media = 0
        self._total_media_hint = 0
        self._emit("preparing", "Preparing processing run", percent=0)
        self._check_cancelled()
        try:
            result = super().run(
                source,
                target,
                force_reprocess=force_reprocess,
                finalize_source=finalize_source,
            )
        except PipelineCancelled:
            raise
        except Exception as exc:
            self._emit("error", f"Pipeline failed: {type(exc).__name__}: {exc}")
            raise
        else:
            self._check_cancelled()
            self._emit(
                "completed",
                "Processing completed",
                percent=100,
                result_status=result.get("status"),
            )
            return result

    def _process_media(
        self,
        source_path: Path,
        extract_root: Path,
        work_root: Path,
        target: str,
        stem: str,
        normalized_name: str,
        metadata_item,
    ) -> dict[str, Any]:
        self._check_cancelled()
        result = super()._process_media(
            source_path,
            extract_root,
            work_root,
            target,
            stem,
            normalized_name,
            metadata_item,
        )
        self._check_cancelled()
        self._completed_media += 1
        self._emit("finalizing", f"Finalizing {source_path.name}", file=source_path.name, percent=90)
        return result

    def _record_failure(self, zip_file, source_path, relative_source, exc, failed):
        if isinstance(exc, PipelineCancelled):
            raise exc
        return super()._record_failure(zip_file, source_path, relative_source, exc, failed)

    def _process_zip(self, zip_file, target: str, *, force_reprocess: bool = False) -> dict[str, Any]:
        self._check_cancelled()
        self._emit("downloading", f"Downloading {zip_file.name}", file=zip_file.name, percent=2)
        self._check_cancelled()
        result = super()._process_zip(zip_file, target, force_reprocess=force_reprocess)
        self._check_cancelled()
        self._emit(
            "zip_completed",
            f"Completed {zip_file.name}",
            file=zip_file.name,
            zip_status=result.get("status"),
            percent=100,
        )
        return result
