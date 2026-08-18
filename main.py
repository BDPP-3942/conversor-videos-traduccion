import os
import sys
import argparse
import tempfile
import shutil
from pathlib import Path
from config import settings
from src.cloud_manager import CloudManager
from src.extractor import ZipExtractor
from src.stt_engine import STTEngine
from src.translator import TextTranslator
from src.vtt_builder import VTTBuilder

def run_pipeline(source_folder_id: str, target_folder_id: str, env_mode: str):
    print("=" * 60)
    print(f" MEDIA PIPELINE STT & TRANSLATION (MODE: {env_mode} | CPU ONLY)")
    print("=" * 60)

    cloud_mgr = CloudManager()
    stt_engine = STTEngine()
    translator = TextTranslator()

    zips = cloud_mgr.list_zip_files(source_folder_id)
    if not zips:
        print("[INFO] No ZIP files found in source Drive folder.")
        return

    print(f"[INFO] Found {len(zips)} ZIP file(s) to process.")

    for zip_file in zips:
        zip_id = zip_file['id']
        zip_name = zip_file['name']
        print(f"\n--- Processing ZIP: {zip_name} ---")

        if env_mode == "PRODUCTION":
            temp_dir_obj = tempfile.TemporaryDirectory()
            work_dir = Path(temp_dir_obj.name)
            print(f"[PROD] Volatile directory created: {work_dir}")
        else:
            temp_dir_obj = None
            work_dir = settings.LOCAL_TEMP_DIR
            work_dir.mkdir(parents=True, exist_ok=True)
            print(f"[LOCAL] Local directory used: {work_dir}")

        try:
            zip_download_path = work_dir / zip_name
            cloud_mgr.download_file(zip_id, zip_download_path)

            mp4_files = ZipExtractor.extract_zip(zip_download_path, work_dir)
            print(f"[EXTRACT] Extracted {len(mp4_files)} .mp4 file(s).")

            for mp4_path in mp4_files:
                print(f"\n -> Processing video: {mp4_path.name}")

                segments_es = stt_engine.transcribe(mp4_path)
                segments_en = translator.translate_segments(segments_es)

                vtt_filename = mp4_path.stem + ".vtt"
                vtt_path = work_dir / vtt_filename
                VTTBuilder.generate_vtt(segments_en, vtt_path)

                print(f"[DRIVE] Uploading extracted MP4...")
                cloud_mgr.upload_file(mp4_path, target_folder_id, mime_type='video/mp4')

                print(f"[DRIVE] Uploading translated VTT...")
                cloud_mgr.upload_file(vtt_path, target_folder_id, mime_type='text/vtt')

                if env_mode == "LOCAL":
                    out_mp4 = settings.LOCAL_OUTPUT_DIR / mp4_path.name
                    out_vtt = settings.LOCAL_OUTPUT_DIR / vtt_path.name
                    shutil.copy(mp4_path, out_mp4)
                    shutil.copy(vtt_path, out_vtt)
                    print(f"[LOCAL] Saved output copy to: {settings.LOCAL_OUTPUT_DIR}")

        finally:
            if temp_dir_obj:
                temp_dir_obj.cleanup()
                print("[PROD] Volatile workspace cleaned up (0 disk space occupied).")

    print("\n" + "=" * 60)
    print(" PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STT + Translation Pipeline for Google Drive")
    parser.add_argument("--source", required=True, help="Source Drive Folder ID")
    parser.add_argument("--target", required=True, help="Target Drive Folder ID")
    parser.add_argument("--mode", choices=["LOCAL", "PRODUCTION"], default=settings.ENV_MODE,
                        help="Execution Mode (LOCAL or PRODUCTION)")

    args = parser.parse_args()
    run_pipeline(args.source, args.target, args.mode)
