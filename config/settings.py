from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def _resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _resolve_base_dir()
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
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"
    whisper_beam_size: int = 5
    whisper_vad_filter: bool = True
    whisper_min_silence_duration_ms: int = 2000
    whisper_subtitle_split_silence_duration_ms: int = 1000
    whisper_condition_on_previous_text: bool = True
    whisper_initial_prompt: str = ""
    whisper_cpu_threads: int = 0
    whisper_repetition_threshold: float = 0.60
    whisper_compression_ratio_threshold: float = 2.4
    whisper_log_prob_threshold: float = -1.0
    whisper_no_speech_threshold: float = 0.6
    whisper_min_repetition_words: int = 8
    whisper_recovery_retries: int = 1
    whisper_recovery_temperatures: tuple[float, ...] = (0.2,)
    translation_provider: str = "mistral"
    translation_fallback_providers: tuple[str, ...] = ("deepl", "mymemory")
    translation_retries: int = 3
    translation_max_retries_per_provider: int = 3
    translation_batch_size: int = 25
    translation_retry_delay_seconds: float = 1.5
    translation_min_request_interval_seconds: float = 0.5
    translation_max_backoff_seconds: float = 16.0
    translation_max_parallel_requests: int = 2
    translation_provider_max_parallel_requests: int = 0
    local_translation_model: str = "madlad400-3b-ct2-int8"
    local_translation_model_dir: Path = BASE_DIR / "tools" / "models" / "translation" / "madlad400-3b-ct2-int8"
    local_translation_model_id: str = "cstr/madlad400-3b-ct2-int8"
    local_translation_model_revision: str = "fd0b55729c074372eb84b52b9309a00dc65c40c4"
    local_translation_device: str = "auto"
    local_translation_compute_type: str = "auto"
    local_translation_beam_size: int = 2
    local_translation_auto_download: bool = False
    max_zip_depth: int = 5
    max_extracted_files: int = 10_000
    max_extracted_size_gb: float = 10.0
    ffmpeg_bin: str = ""
    ffmpeg_preset: str = "medium"
    ffmpeg_crf: int = 23
    ffmpeg_audio_bitrate: str = "256k"
    generate_webm: bool = False
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
    automatic_output_deduplication: bool = False
    max_parallel_videos: int = 0
    duplicate_name_similarity_threshold: float = 0.82
    duplicate_duration_tolerance_seconds: float = 1.5
    duplicate_visual_similarity_threshold: float = 0.91
    ffmpeg_avoid_reencode: bool = True
    tts_enabled: bool = False
    tts_required: bool = False
    tts_provider: str = "kokoro"
    tts_voice: str = "am_michael"
    tts_model_path: Path = BASE_DIR / "tools" / "tts" / "kokoro-v1.0.onnx"
    tts_voices_path: Path = BASE_DIR / "tools" / "tts" / "voices-v1.0.bin"
    tts_speed: float = 1.0
    tts_max_speed: float = 1.35
    tts_duration_tolerance: float = 0.02
    tts_sample_rate: int = 24000
    tts_audio_bitrate: str = "192k"
    tts_webm_audio_bitrate: str = "192k"
    tts_generate_webm: bool = False
    google_credentials_file: Path = BASE_DIR / "secrets" / "providers" / "google" / "default" / "credentials.json"
    google_token_file: Path = BASE_DIR / "secrets" / "providers" / "google" / "default" / "token.json"
    rclone_config_file: Path = BASE_DIR / "secrets" / "rclone" / "rclone.conf"
    rclone_binary_file: Path = BASE_DIR / "tools" / "rclone" / "rclone"
    rclone_remote: str = "remote_drive"
    provider_profile_dir: Path = BASE_DIR / "secrets" / "providers"
    run_lock_file: Path = BASE_DIR / "storage" / "state" / "run.lock"
    auto_bootstrap_rclone: bool = True
    auto_update_rclone: bool = False
    auto_tune_resources: bool = True
