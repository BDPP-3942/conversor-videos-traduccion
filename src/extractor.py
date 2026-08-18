import zipfile
from pathlib import Path
from typing import List

class ZipExtractor:
    @staticmethod
    def extract_zip(zip_path: Path, extract_to: Path) -> List[Path]:
        extracted_mp4s = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.mp4') and not file_info.filename.startswith('__MACOSX'):
                    extracted_mp4s.append(extract_to / file_info.filename)
        return extracted_mp4s
