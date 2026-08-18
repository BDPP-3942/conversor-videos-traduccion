import argparse
import json
import logging
import shutil
import sys
import tempfile

from pathlib import Path
from typing import Any, Dict, List

from config import settings

from src.cloud_manager import CloudManager
from src.extractor import ZipExtractor
from src.file_naming import FileNameFormatter
from src.stt_engine import STTEngine
from src.translator import TextTranslator
from src.vtt_builder import VTTBuilder


logger = logging.getLogger(__name__)


# ============================================================
# LOGGING
# ============================================================

def configure_logging() -> None:
    """
    Configura logging para ejecución manual,
    cron, Task Scheduler y n8n.
    """

    settings.LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = (
        settings.LOG_DIR
        / "pipeline.log"
    )

    logging.basicConfig(
        level=getattr(
            logging,
            settings.LOG_LEVEL,
            logging.INFO,
        ),
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s - "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(
                sys.stdout
            ),
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            ),
        ],
    )


# ============================================================
# PROCESAR VIDEO
# ============================================================

def process_video(
    mp4_path: Path,
    work_dir: Path,
    target_folder_id: str,
    cloud_manager: CloudManager,
    stt_engine: STTEngine,
    translator: TextTranslator,
) -> Dict[str, Any]:

    logger.info(
        "Processing video: %s",
        mp4_path.name,
    )

    # --------------------------------------------------------
    # STT
    # --------------------------------------------------------

    segments_source = (
        stt_engine.transcribe(
            mp4_path
        )
    )

    if not segments_source:
        raise RuntimeError(
            f"No STT segments generated for "
            f"{mp4_path.name}"
        )

    # --------------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------------

    segments_target = (
        translator.translate_segments(
            segments_source
        )
    )

    # --------------------------------------------------------
    # VTT NAME
    # --------------------------------------------------------

    vtt_filename = (
        FileNameFormatter.generate_vtt_name(
            mp4_path.name,
            settings.TARGET_LANG,
        )
    )

    vtt_path = (
        work_dir
        / vtt_filename
    )

    # --------------------------------------------------------
    # VTT
    # --------------------------------------------------------

    VTTBuilder.generate_vtt(
        segments_target,
        vtt_path,
    )

    # --------------------------------------------------------
    # UPLOAD MP4
    # --------------------------------------------------------

    cloud_manager.upload_file(
        mp4_path,
        target_folder_id,
        mime_type=settings.MIME_MP4,
    )

    # --------------------------------------------------------
    # UPLOAD VTT
    # --------------------------------------------------------

    cloud_manager.upload_file(
        vtt_path,
        target_folder_id,
        mime_type=settings.MIME_VTT,
    )

    # --------------------------------------------------------
    # LOCAL COPY
    # --------------------------------------------------------

    if settings.ENV_MODE == "LOCAL":

        output_mp4 = (
            settings.LOCAL_OUTPUT_DIR
            / mp4_path.name
        )

        output_vtt = (
            settings.LOCAL_OUTPUT_DIR
            / vtt_path.name
        )

        shutil.copy2(
            mp4_path,
            output_mp4,
        )

        shutil.copy2(
            vtt_path,
            output_vtt,
        )

    logger.info(
        "Video completed: %s",
        mp4_path.name,
    )

    return {
        "video": mp4_path.name,
        "vtt": vtt_path.name,
        "segments": len(
            segments_target
        ),
        "status": "success",
    }


# ============================================================
# PROCESAR ZIP
# ============================================================

def process_zip(
    zip_file: Dict[str, str],
    source_folder_id: str,
    target_folder_id: str,
    env_mode: str,
    cloud_manager: CloudManager,
    stt_engine: STTEngine,
    translator: TextTranslator,
) -> Dict[str, Any]:

    zip_id = zip_file["id"]
    zip_name = zip_file["name"]

    logger.info(
        "Processing ZIP: %s",
        zip_name,
    )

    temp_dir_obj = None

    if env_mode == "PRODUCTION":

        temp_dir_obj = (
            tempfile.TemporaryDirectory()
        )

        work_dir = Path(
            temp_dir_obj.name
        )

    else:

        work_dir = (
            settings.LOCAL_TEMP_DIR
            / Path(zip_name).stem
        )

        if work_dir.exists():
            shutil.rmtree(
                work_dir
            )

        work_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    try:

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        zip_download_path = (
            work_dir
            / zip_name
        )

        cloud_manager.download_file(
            zip_id,
            zip_download_path,
        )

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        extractor = ZipExtractor()

        extraction = (
            extractor.extract_zip(
                zip_download_path,
                work_dir,
            )
        )

        logger.info(
            "ZIP extracted: %d MP4, "
            "%d nested ZIP",
            len(extraction.videos),
            len(extraction.nested_zips),
        )

        # ----------------------------------------------------
        # PROCESS VIDEOS
        # ----------------------------------------------------

        processed_videos: List[
            Dict[str, Any]
        ] = []

        failed_videos: List[
            Dict[str, Any]
        ] = []

        for mp4_path in extraction.videos:

            try:

                result = process_video(
                    mp4_path=mp4_path,
                    work_dir=work_dir,
                    target_folder_id=(
                        target_folder_id
                    ),
                    cloud_manager=(
                        cloud_manager
                    ),
                    stt_engine=stt_engine,
                    translator=translator,
                )

                processed_videos.append(
                    result
                )

            except Exception as exc:

                logger.exception(
                    "Video processing failed: %s",
                    mp4_path.name,
                )

                failed_videos.append(
                    {
                        "video": (
                            mp4_path.name
                        ),
                        "error": str(exc),
                    }
                )

        status = (
            "success"
            if not failed_videos
            else "partial"
        )

        if not extraction.videos:
            status = "error"

        return {
            "zip": zip_name,
            "status": status,
            "nested_zips": len(
                extraction.nested_zips
            ),
            "videos_found": len(
                extraction.videos
            ),
            "videos_processed": len(
                processed_videos
            ),
            "videos_failed": len(
                failed_videos
            ),
            "videos": processed_videos,
            "errors": failed_videos,
            "max_zip_depth": (
                extraction.max_depth_reached
            ),
        }

    finally:

        if temp_dir_obj:
            temp_dir_obj.cleanup()

        elif work_dir.exists():
            shutil.rmtree(
                work_dir,
                ignore_errors=True,
            )


# ============================================================
# PIPELINE
# ============================================================

def run_pipeline(
    source_folder_id: str,
    target_folder_id: str,
    env_mode: str,
) -> Dict[str, Any]:

    logger.info(
        "Starting pipeline - mode=%s",
        env_mode,
    )

    cloud_manager = CloudManager()

    stt_engine = STTEngine()

    translator = TextTranslator()

    zips = (
        cloud_manager.list_zip_files(
            source_folder_id
        )
    )

    if not zips:

        logger.info(
            "No ZIP files found."
        )

        return {
            "status": "success",
            "message": "No ZIP files found",
            "zips_found": 0,
            "zips_processed": 0,
        }

    logger.info(
        "Found %d ZIP file(s)",
        len(zips),
    )

    zip_results = []

    for zip_file in zips:

        result = process_zip(
            zip_file=zip_file,
            source_folder_id=(
                source_folder_id
            ),
            target_folder_id=(
                target_folder_id
            ),
            env_mode=env_mode,
            cloud_manager=cloud_manager,
            stt_engine=stt_engine,
            translator=translator,
        )

        zip_results.append(
            result
        )

    failed = [
        result
        for result in zip_results
        if result["status"] == "error"
    ]

    partial = [
        result
        for result in zip_results
        if result["status"] == "partial"
    ]

    if failed:
        overall_status = "error"

    elif partial:
        overall_status = "partial"

    else:
        overall_status = "success"

    return {
        "status": overall_status,
        "zips_found": len(zips),
        "zips_processed": len(
            zip_results
        ),
        "zips": zip_results,
    }


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "STT + Translation + VTT "
            "Media Processing Pipeline"
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        help=(
            "Google Drive source folder ID"
        ),
    )

    parser.add_argument(
        "--target",
        required=True,
        help=(
            "Google Drive target folder ID"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=[
            "LOCAL",
            "PRODUCTION",
        ],
        default=settings.ENV_MODE,
        help=(
            "Execution mode"
        ),
    )

    return parser


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    settings.ensure_directories()

    configure_logging()

    parser = build_parser()

    args = parser.parse_args()

    try:

        result = run_pipeline(
            source_folder_id=args.source,
            target_folder_id=args.target,
            env_mode=args.mode,
        )

        # Muy importante para n8n:
        # el resultado se puede consumir como JSON.
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        if result["status"] == "error":
            return 1

        if result["status"] == "partial":
            return 2

        return 0

    except Exception as exc:

        logger.exception(
            "Pipeline failed"
        )

        error_result = {
            "status": "error",
            "error": str(exc),
        }

        print(
            json.dumps(
                error_result,
                ensure_ascii=False,
                indent=2,
            )
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )