from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent.parent
)
CONFIG_DIR = BASE_DIR / "config"
SECRETS_DIR = BASE_DIR / "secrets"
STORAGE_DIR = BASE_DIR / "storage"


@dataclass(frozen=True)
class AppSettings:
    provider: str = "local"
    source: str = "local://storage/input"
    target: str = "local://storage/output"
    source_lang: str = "es"
    target_lang: str = "en"
    log_level: str = "INFO"
    whisper_model: str = "auto"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_beam_size: int = 5
    whisper_vad_filter: bool = True
    whisper_condition_on_previous_text: bool = True
    whisper_initial_prompt: str = ""
    whisper_cpu_threads: int = 0
    translation_provider: str = "google"
    translation_fallback_providers: tuple[str, ...] = ()
    translation_retries: int = 5
    translation_max_retries_per_provider: int = 0
    translation_batch_size: int = 0
    translation_retry_delay_seconds: float = 1.5
    translation_min_request_interval_seconds: float = 0.35
    translation_max_backoff_seconds: float = 16.0
    max_zip_depth: int = 5
    max_extracted_files: int = 10_000
    max_extracted_size_gb: float = 10.0
    ffmpeg_bin: str = ""
    ffmpeg_preset: str = "medium"
    ffmpeg_crf: int = 23
    ffmpeg_audio_bitrate: str = "256k"
    generate_webm: bool = True
    secondary_video_extension: str = "webm"
    secondary_video_codec: str = "libvpx-vp9"
    secondary_video_crf: int = 0
    secondary_video_max_width: int = 0
    secondary_video_fps: int = 0
    secondary_video_audio_codec: str = "libopus"
    secondary_video_audio_bitrate: str = "256k"
    secondary_video_cpu_used: int = 5
    ffmpeg_timeout_seconds: int = 7200
    local_retain_sources: bool = True
    local_input_min_age_seconds: int = 60
    source_folder_id: str = ""
    target_folder_id: str = ""
    archive_folder_id: str = ""
    original_transcript_subdir: str = "original_transcriptions"
    resume_enabled: bool = True
    normalize_legacy_names: bool = True
    rename_processed_duplicates: bool = True
    max_parallel_videos: int = 0
    duplicate_name_similarity_threshold: float = 0.82
    duplicate_duration_tolerance_seconds: float = 1.5
    duplicate_visual_similarity_threshold: float = 0.91
    ffmpeg_avoid_reencode: bool = True
    google_credentials_file: Path = SECRETS_DIR / "providers" / "google" / "default" / "credentials.json"
    google_token_file: Path = SECRETS_DIR / "providers" / "google" / "default" / "token.json"
    google_profile: str = "default"
    rclone_config_file: Path = SECRETS_DIR / "rclone" / "rclone.conf"
    rclone_binary_file: Path = BASE_DIR / "tools" / "rclone" / "rclone"
    rclone_remote: str = "remote_drive"
    provider_profile_dir: Path = SECRETS_DIR / "providers"
    run_lock_file: Path = STORAGE_DIR / "state" / "run.lock"
    auto_bootstrap_rclone: bool = True
    auto_update_rclone: bool = False
    auto_tune_resources: bool = True
    resource_profile: str = "auto"
    detected_logical_cpus: int = 0
    detected_memory_gb: float = 0.0

    @property
    def max_extracted_size_bytes(self) -> int:
        return int(self.max_extracted_size_gb * 1024**3)

    @property
    def effective_translation_retries(self) -> int:
        configured = self.translation_max_retries_per_provider or self.translation_retries
        return max(1, int(configured))

    @classmethod
    def from_environment(cls) -> AppSettings:
        fallback_raw = os.getenv("TRANSLATION_FALLBACK_PROVIDERS", "")
        fallback = tuple(item.strip() for item in fallback_raw.split(",") if item.strip())
        return cls(
            provider=os.getenv("STORAGE_PROVIDER", cls.provider),
            source=os.getenv("SOURCE_URI", cls.source),
            target=os.getenv("TARGET_URI", cls.target),
            source_lang=os.getenv("SOURCE_LANG", cls.source_lang),
            target_lang=os.getenv("TARGET_LANG", cls.target_lang),
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            whisper_model=os.getenv("WHISPER_MODEL", cls.whisper_model),
            whisper_device=os.getenv("WHISPER_DEVICE", cls.whisper_device),
            whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", cls.whisper_compute_type),
            whisper_beam_size=int(os.getenv("WHISPER_BEAM_SIZE", cls.whisper_beam_size)),
            whisper_vad_filter=os.getenv("WHISPER_VAD_FILTER", "true").lower() == "true",
            whisper_condition_on_previous_text=(
                os.getenv("WHISPER_CONDITION_ON_PREVIOUS_TEXT", "false").lower() == "true"
            ),
            whisper_initial_prompt=os.getenv("WHISPER_INITIAL_PROMPT", cls.whisper_initial_prompt),
            whisper_cpu_threads=int(os.getenv("WHISPER_CPU_THREADS", cls.whisper_cpu_threads)),
            translation_provider=os.getenv("TRANSLATION_PROVIDER", cls.translation_provider),
            translation_fallback_providers=fallback,
            translation_retries=int(os.getenv("TRANSLATION_RETRIES", cls.translation_retries)),
            translation_max_retries_per_provider=int(
                os.getenv("TRANSLATION_MAX_RETRIES_PER_PROVIDER", cls.translation_max_retries_per_provider)
            ),
            translation_batch_size=int(os.getenv("TRANSLATION_BATCH_SIZE", cls.translation_batch_size)),
            translation_retry_delay_seconds=float(
                os.getenv("TRANSLATION_RETRY_DELAY_SECONDS", cls.translation_retry_delay_seconds)
            ),
            translation_min_request_interval_seconds=float(
                os.getenv("TRANSLATION_MIN_REQUEST_INTERVAL_SECONDS", cls.translation_min_request_interval_seconds)
            ),
            translation_max_backoff_seconds=float(
                os.getenv("TRANSLATION_MAX_BACKOFF_SECONDS", cls.translation_max_backoff_seconds)
            ),
            max_zip_depth=int(os.getenv("MAX_ZIP_DEPTH", cls.max_zip_depth)),
            max_extracted_files=int(os.getenv("MAX_EXTRACTED_FILES", cls.max_extracted_files)),
            max_extracted_size_gb=float(os.getenv("MAX_EXTRACTED_SIZE_GB", cls.max_extracted_size_gb)),
            ffmpeg_bin=os.getenv("FFMPEG_BIN", cls.ffmpeg_bin),
            ffmpeg_preset=os.getenv("FFMPEG_PRESET", cls.ffmpeg_preset),
            ffmpeg_crf=int(os.getenv("FFMPEG_CRF", cls.ffmpeg_crf)),
            ffmpeg_audio_bitrate=os.getenv("FFMPEG_AUDIO_BITRATE", cls.ffmpeg_audio_bitrate),
            generate_webm=os.getenv("GENERATE_WEBM", "true").lower() == "true",
            secondary_video_extension=os.getenv("SECONDARY_VIDEO_EXTENSION", cls.secondary_video_extension),
            secondary_video_codec=os.getenv("SECONDARY_VIDEO_CODEC", cls.secondary_video_codec),
            secondary_video_crf=int(os.getenv("SECONDARY_VIDEO_CRF", cls.secondary_video_crf)),
            secondary_video_max_width=int(os.getenv("SECONDARY_VIDEO_MAX_WIDTH", cls.secondary_video_max_width)),
            secondary_video_fps=int(os.getenv("SECONDARY_VIDEO_FPS", cls.secondary_video_fps)),
            secondary_video_audio_codec=os.getenv("SECONDARY_VIDEO_AUDIO_CODEC", cls.secondary_video_audio_codec),
            secondary_video_audio_bitrate=os.getenv("SECONDARY_VIDEO_AUDIO_BITRATE", cls.secondary_video_audio_bitrate),
            secondary_video_cpu_used=int(os.getenv("SECONDARY_VIDEO_CPU_USED", cls.secondary_video_cpu_used)),
            ffmpeg_timeout_seconds=int(os.getenv("FFMPEG_TIMEOUT_SECONDS", cls.ffmpeg_timeout_seconds)),
            local_retain_sources=os.getenv("LOCAL_RETAIN_SOURCES", "true").lower() == "true",
            local_input_min_age_seconds=int(os.getenv("LOCAL_INPUT_MIN_AGE_SECONDS", cls.local_input_min_age_seconds)),
            source_folder_id=os.getenv("GDRIVE_SOURCE_FOLDER_ID", ""),
            target_folder_id=os.getenv("GDRIVE_TARGET_FOLDER_ID", ""),
            archive_folder_id=os.getenv("GDRIVE_ARCHIVE_FOLDER_ID", ""),
            original_transcript_subdir=os.getenv("ORIGINAL_TRANSCRIPT_SUBDIR", cls.original_transcript_subdir),
            resume_enabled=os.getenv("RESUME_ENABLED", "true").lower() == "true",
            normalize_legacy_names=os.getenv("NORMALIZE_LEGACY_NAMES", "true").lower() == "true",
            rename_processed_duplicates=os.getenv("RENAME_PROCESSED_DUPLICATES", "true").lower() == "true",
            max_parallel_videos=int(os.getenv("MAX_PARALLEL_VIDEOS", cls.max_parallel_videos)),
            duplicate_name_similarity_threshold=float(
                os.getenv("DUPLICATE_NAME_SIMILARITY_THRESHOLD", cls.duplicate_name_similarity_threshold)
            ),
            duplicate_duration_tolerance_seconds=float(
                os.getenv("DUPLICATE_DURATION_TOLERANCE_SECONDS", cls.duplicate_duration_tolerance_seconds)
            ),
            duplicate_visual_similarity_threshold=float(
                os.getenv("DUPLICATE_VISUAL_SIMILARITY_THRESHOLD", cls.duplicate_visual_similarity_threshold)
            ),
            ffmpeg_avoid_reencode=os.getenv("FFMPEG_AVOID_REENCODE", "true").lower() == "true",
            google_credentials_file=Path(os.getenv("GOOGLE_CREDENTIALS_FILE", cls.google_credentials_file)),
            google_token_file=Path(os.getenv("GOOGLE_TOKEN_FILE", cls.google_token_file)),
            google_profile=os.getenv("GOOGLE_PROFILE", cls.google_profile),
            rclone_config_file=Path(os.getenv("RCLONE_CONFIG_FILE", cls.rclone_config_file)),
            rclone_binary_file=Path(os.getenv("RCLONE_BINARY_FILE", cls.rclone_binary_file)),
            rclone_remote=os.getenv("RCLONE_REMOTE", cls.rclone_remote),
            run_lock_file=Path(os.getenv("RUN_LOCK_FILE", cls.run_lock_file)),
            auto_bootstrap_rclone=os.getenv("AUTO_BOOTSTRAP_RCLONE", "true").lower() == "true",
            auto_update_rclone=os.getenv("AUTO_UPDATE_RCLONE", "false").lower() == "true",
            auto_tune_resources=os.getenv("AUTO_TUNE_RESOURCES", "true").lower() == "true",
            provider_profile_dir=Path(os.getenv("PROVIDER_PROFILE_DIR", cls.provider_profile_dir)),
        )


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (BASE_DIR / path).resolve()


def local_storage_paths() -> dict[str, Path]:
    return {
        "input": STORAGE_DIR / "input",
        "output": STORAGE_DIR / "output",
        "work": STORAGE_DIR / "work",
        "failures": STORAGE_DIR / "failures",
        "archive": STORAGE_DIR / "archive",
        "archive_sources": STORAGE_DIR / "archive" / "sources",
        "logs": STORAGE_DIR / "logs",
        "state": STORAGE_DIR / "state",
        "manifests": STORAGE_DIR / "output/_manifests",
    }


def ensure_directories() -> None:
    for path in local_storage_paths().values():
        path.mkdir(parents=True, exist_ok=True)
    (SECRETS_DIR / "google").mkdir(parents=True, exist_ok=True)
