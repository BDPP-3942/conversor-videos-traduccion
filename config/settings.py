from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
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
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_beam_size: int = 1
    whisper_vad_filter: bool = True
    whisper_condition_on_previous_text: bool = False
    whisper_cpu_threads: int = 0
    translation_retries: int = 10
    translation_batch_size: int = 40
    translation_retry_delay_seconds: float = 2.0
    max_zip_depth: int = 5
    max_extracted_files: int = 10_000
    max_extracted_size_gb: float = 10.0
    ffmpeg_bin: str = ""
    ffmpeg_preset: str = "medium"
    ffmpeg_crf: int = 23
    ffmpeg_audio_bitrate: str = "192k"
    ffmpeg_mp3_quality: int = 2
    ffmpeg_timeout_seconds: int = 7200
    local_retain_sources: bool = True
    local_input_min_age_seconds: int = 60
    source_folder_id: str = ""
    target_folder_id: str = ""
    archive_folder_id: str = ""
    original_transcript_subdir: str = "original_transcriptions"
    resume_enabled: bool = True
    normalize_legacy_names: bool = True
    max_parallel_videos: int = 2
    ffmpeg_avoid_reencode: bool = True
    google_credentials_file: Path = SECRETS_DIR / "google" / "credentials.json"
    google_token_file: Path = SECRETS_DIR / "google" / "token.json"
    rclone_config_file: Path = CONFIG_DIR / "rclone.conf"
    rclone_remote: str = "remote_drive"

    @property
    def max_extracted_size_bytes(self) -> int:
        return int(self.max_extracted_size_gb * 1024**3)

    @classmethod
    def from_environment(cls) -> "AppSettings":
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
            whisper_condition_on_previous_text=os.getenv("WHISPER_CONDITION_ON_PREVIOUS_TEXT", "false").lower() == "true",
            whisper_cpu_threads=int(os.getenv("WHISPER_CPU_THREADS", cls.whisper_cpu_threads)),
            translation_retries=int(
                os.getenv("TRANSLATION_RETRIES", cls.translation_retries)
            ),
            translation_batch_size=int(os.getenv("TRANSLATION_BATCH_SIZE", cls.translation_batch_size)),
            translation_retry_delay_seconds=float(
                os.getenv("TRANSLATION_RETRY_DELAY_SECONDS", cls.translation_retry_delay_seconds)
            ),
            max_zip_depth=int(os.getenv("MAX_ZIP_DEPTH", cls.max_zip_depth)),
            max_extracted_files=int(
                os.getenv("MAX_EXTRACTED_FILES", cls.max_extracted_files)
            ),
            max_extracted_size_gb=float(
                os.getenv("MAX_EXTRACTED_SIZE_GB", cls.max_extracted_size_gb)
            ),
            ffmpeg_bin=os.getenv("FFMPEG_BIN", cls.ffmpeg_bin),
            ffmpeg_preset=os.getenv("FFMPEG_PRESET", cls.ffmpeg_preset),
            ffmpeg_crf=int(os.getenv("FFMPEG_CRF", cls.ffmpeg_crf)),
            ffmpeg_audio_bitrate=os.getenv(
                "FFMPEG_AUDIO_BITRATE", cls.ffmpeg_audio_bitrate
            ),
            ffmpeg_mp3_quality=int(
                os.getenv("FFMPEG_MP3_QUALITY", cls.ffmpeg_mp3_quality)
            ),
            ffmpeg_timeout_seconds=int(
                os.getenv("FFMPEG_TIMEOUT_SECONDS", cls.ffmpeg_timeout_seconds)
            ),
            local_retain_sources=os.getenv(
                "LOCAL_RETAIN_SOURCES", "true"
            ).lower()
            == "true",
            local_input_min_age_seconds=int(
                os.getenv("LOCAL_INPUT_MIN_AGE_SECONDS", cls.local_input_min_age_seconds)
            ),
            source_folder_id=os.getenv("GDRIVE_SOURCE_FOLDER_ID", ""),
            target_folder_id=os.getenv("GDRIVE_TARGET_FOLDER_ID", ""),
            archive_folder_id=os.getenv("GDRIVE_ARCHIVE_FOLDER_ID", ""),
            original_transcript_subdir=os.getenv(
                "ORIGINAL_TRANSCRIPT_SUBDIR", cls.original_transcript_subdir
            ),
            resume_enabled=os.getenv("RESUME_ENABLED", "true").lower() == "true",
            normalize_legacy_names=os.getenv("NORMALIZE_LEGACY_NAMES", "true").lower() == "true",
            max_parallel_videos=int(os.getenv("MAX_PARALLEL_VIDEOS", cls.max_parallel_videos)),
            ffmpeg_avoid_reencode=os.getenv("FFMPEG_AVOID_REENCODE", "true").lower() == "true",
            google_credentials_file=Path(
                os.getenv("GOOGLE_CREDENTIALS_FILE", cls.google_credentials_file)
            ),
            google_token_file=Path(os.getenv("GOOGLE_TOKEN_FILE", cls.google_token_file)),
            rclone_config_file=Path(
                os.getenv("RCLONE_CONFIG_FILE", cls.rclone_config_file)
            ),
            rclone_remote=os.getenv("RCLONE_REMOTE", cls.rclone_remote),
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
