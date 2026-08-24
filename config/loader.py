from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tomllib

from config.settings import AppSettings, BASE_DIR


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(BASE_DIR / ".env", override=False)


def load_settings(config_path: Path | None = None) -> AppSettings:
    _load_dotenv()
    path = config_path or (BASE_DIR / "config" / "app.toml")
    if not path.is_file():
        settings = AppSettings()
    else:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        app = data.get("app", {})
        local = data.get("local", {})
        google = data.get("google_drive", {})
        rclone = data.get("rclone", {})
        providers = data.get("providers", {})
        processing = data.get("processing", {})
        ffmpeg = data.get("ffmpeg", {})
        workflow = data.get("workflow", {})
        runtime_cfg = data.get("runtime", {})

        settings = AppSettings(
            provider=str(app.get("provider", "local")),
            source=str(app.get("source", "local://storage/input")),
            target=str(app.get("target", "local://storage/output")),
            source_lang=str(app.get("source_lang", "es")),
            target_lang=str(app.get("target_lang", "en")),
            log_level=str(app.get("log_level", "INFO")).upper(),
            whisper_model=str(processing.get("whisper_model", "small")),
            whisper_device=str(processing.get("whisper_device", "cpu")),
            whisper_compute_type=str(processing.get("whisper_compute_type", "int8")),
            whisper_beam_size=int(processing.get("whisper_beam_size", 1)),
            whisper_vad_filter=bool(processing.get("whisper_vad_filter", True)),
            whisper_condition_on_previous_text=bool(processing.get(
                "whisper_condition_on_previous_text",
                False
            )),
            whisper_cpu_threads=int(processing.get("whisper_cpu_threads", 0)),
            translation_retries=int(processing.get("translation_retries", 10)),
            translation_batch_size=int(processing.get("translation_batch_size", 40)),
            translation_retry_delay_seconds=float(
                processing.get("translation_retry_delay_seconds", 2.0)
            ),
            max_zip_depth=int(processing.get("max_zip_depth", 3)),
            max_extracted_files=int(processing.get("max_extracted_files", 10000)),
            max_extracted_size_gb=float(processing.get("max_extracted_size_gb", 10.0)),
            ffmpeg_bin=str(ffmpeg.get("bin", "")),
            ffmpeg_preset=str(ffmpeg.get("preset", "medium")),
            ffmpeg_crf=int(ffmpeg.get("crf", 23)),
            ffmpeg_audio_bitrate=str(ffmpeg.get("audio_bitrate", "192k")),
            ffmpeg_mp3_quality=int(ffmpeg.get("mp3_quality", 2)),
            ffmpeg_timeout_seconds=int(ffmpeg.get("timeout_seconds", 7200)),
            local_retain_sources=bool(local.get("retain_sources", True)),
            local_input_min_age_seconds=int(local.get("input_min_age_seconds", 60)),
            source_folder_id=str(google.get("source_folder_id", "")),
            target_folder_id=str(google.get("target_folder_id", "")),
            archive_folder_id=str(google.get("archive_folder_id", "")),
            original_transcript_subdir=str(
                google.get("original_transcript_subdir", "original_transcriptions")
            ),
            resume_enabled=bool(workflow.get("resume_enabled", True)),
            normalize_legacy_names=bool(workflow.get("normalize_legacy_names", True)),
            max_parallel_videos=int(workflow.get("max_parallel_videos", 2)),
            duplicate_name_similarity_threshold=float(workflow.get(
                "duplicate_name_similarity_threshold",
                0.82
            )),
            duplicate_duration_tolerance_seconds=float(workflow.get(
                "duplicate_duration_tolerance_seconds",
                1.5
            )),
            duplicate_visual_similarity_threshold=float(workflow.get(
                "duplicate_visual_similarity_threshold",
                0.91
            )),
            google_credentials_file=Path(
                str(google.get(
                    "credentials_file",
                    "secrets/providers/google/default/credentials.json"
                ))
            ),
            google_token_file=Path(
                str(google.get("token_file", "secrets/providers/google/default/token.json"))
            ),
            rclone_config_file=Path(str(rclone.get("config_file", "secrets/rclone/rclone.conf"))),
            rclone_binary_file=Path(str(rclone.get("binary_file", "tools/rclone/rclone"))),
            rclone_remote=str(rclone.get("remote", "remote_drive")),
            provider_profile_dir=Path(str(providers.get("profile_dir", "secrets/providers"))),
            ffmpeg_avoid_reencode=bool(ffmpeg.get("avoid_reencode", True)),
            run_lock_file=Path(str(runtime_cfg.get("run_lock_file", "storage/state/run.lock"))),
            auto_bootstrap_rclone=bool(runtime_cfg.get("auto_bootstrap_rclone", True)),
            auto_update_rclone=bool(runtime_cfg.get("auto_update_rclone", False)),
        )

    settings = _apply_runtime_provider(settings)
    return _apply_environment_overrides(settings)


def _apply_environment_overrides(settings: AppSettings) -> AppSettings:
    env = AppSettings.from_environment()
    replacements = {}
    mapping = {
        "STORAGE_PROVIDER": "provider",
        "SOURCE_URI": "source",
        "TARGET_URI": "target",
        "SOURCE_LANG": "source_lang",
        "TARGET_LANG": "target_lang",
        "LOG_LEVEL": "log_level",
        "WHISPER_MODEL": "whisper_model",
        "WHISPER_DEVICE": "whisper_device",
        "WHISPER_COMPUTE_TYPE": "whisper_compute_type",
        "WHISPER_BEAM_SIZE": "whisper_beam_size",
        "WHISPER_VAD_FILTER": "whisper_vad_filter",
        "WHISPER_CONDITION_ON_PREVIOUS_TEXT": "whisper_condition_on_previous_text",
        "WHISPER_CPU_THREADS": "whisper_cpu_threads",
        "TRANSLATION_RETRIES": "translation_retries",
        "TRANSLATION_BATCH_SIZE": "translation_batch_size",
        "TRANSLATION_RETRY_DELAY_SECONDS": "translation_retry_delay_seconds",
        "MAX_ZIP_DEPTH": "max_zip_depth",
        "MAX_EXTRACTED_FILES": "max_extracted_files",
        "MAX_EXTRACTED_SIZE_GB": "max_extracted_size_gb",
        "FFMPEG_BIN": "ffmpeg_bin",
        "FFMPEG_PRESET": "ffmpeg_preset",
        "FFMPEG_CRF": "ffmpeg_crf",
        "FFMPEG_AUDIO_BITRATE": "ffmpeg_audio_bitrate",
        "FFMPEG_MP3_QUALITY": "ffmpeg_mp3_quality",
        "FFMPEG_TIMEOUT_SECONDS": "ffmpeg_timeout_seconds",
        "GDRIVE_SOURCE_FOLDER_ID": "source_folder_id",
        "GDRIVE_TARGET_FOLDER_ID": "target_folder_id",
        "GDRIVE_ARCHIVE_FOLDER_ID": "archive_folder_id",
        "ORIGINAL_TRANSCRIPT_SUBDIR": "original_transcript_subdir",
        "GOOGLE_CREDENTIALS_FILE": "google_credentials_file",
        "GOOGLE_TOKEN_FILE": "google_token_file",
        "RCLONE_CONFIG_FILE": "rclone_config_file",
        "RCLONE_BINARY_FILE": "rclone_binary_file",
        "RCLONE_REMOTE": "rclone_remote",
        "PROVIDER_PROFILE_DIR": "provider_profile_dir",
        "RESUME_ENABLED": "resume_enabled",
        "NORMALIZE_LEGACY_NAMES": "normalize_legacy_names",
        "MAX_PARALLEL_VIDEOS": "max_parallel_videos",
        "DUPLICATE_NAME_SIMILARITY_THRESHOLD": "duplicate_name_similarity_threshold",
        "DUPLICATE_DURATION_TOLERANCE_SECONDS": "duplicate_duration_tolerance_seconds",
        "DUPLICATE_VISUAL_SIMILARITY_THRESHOLD": "duplicate_visual_similarity_threshold",
        "FFMPEG_AVOID_REENCODE": "ffmpeg_avoid_reencode",
        "RUN_LOCK_FILE": "run_lock_file",
        "AUTO_BOOTSTRAP_RCLONE": "auto_bootstrap_rclone",
        "AUTO_UPDATE_RCLONE": "auto_update_rclone",
    }
    import os

    for env_name, field_name in mapping.items():
        if env_name in os.environ:
            replacements[field_name] = getattr(env, field_name)
    if "LOCAL_RETAIN_SOURCES" in os.environ:
        replacements["local_retain_sources"] = env.local_retain_sources
    if "LOCAL_INPUT_MIN_AGE_SECONDS" in os.environ:
        replacements["local_input_min_age_seconds"] = env.local_input_min_age_seconds
    return replace(settings, **replacements)


def _apply_runtime_provider(settings: AppSettings) -> AppSettings:
    runtime_path = BASE_DIR / "config" / "runtime.toml"
    if not runtime_path.is_file():
        return settings
    try:
        runtime = tomllib.loads(runtime_path.read_text(encoding="utf-8")).get("active", {})
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(f"Invalid runtime provider file: {runtime_path}") from exc
    if not isinstance(runtime, dict):
        return settings
    values = {}
    for name in ("provider", "source", "target", "rclone_remote"):
        if name in runtime:
            values[name] = str(runtime[name])
    if "archive" in runtime and runtime.get("provider") in {"google_drive", "gdrive"}:
        values["archive_folder_id"] = str(runtime.get("archive", ""))
    if runtime.get("profile") or runtime.get("provider") in {"google_drive", "gdrive"}:
        profile = str(runtime.get("profile", settings.google_profile or "default"))
        values["google_profile"] = profile
        values["google_credentials_file"] = (
            settings.provider_profile_dir / "google" / profile / "credentials.json"
        )
        values["google_token_file"] = (
            settings.provider_profile_dir / "google" / profile / "token.json"
        )
        if "archive" in runtime:
            values["archive_folder_id"] = str(runtime.get("archive", ""))
    return replace(settings, **values) if values else settings
