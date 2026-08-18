import json
import mimetypes
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from src.rclone_installer import ensure_rclone_binary

class CloudManager:
    def __init__(self, remote_name: str = "remote_drive"):
        self.rclone_bin = ensure_rclone_binary()
        self.config_path = Path(__file__).resolve().parent.parent / "config" / "rclone.conf"
        self.remote_name = remote_name

    @staticmethod
    def _detect_mime_type(file_path: Path) -> Optional[str]:
        mime_type, _ = mimetypes.guess_type(file_path.name)
        return mime_type

    def _run_cmd(self, args: List[str]) -> str:
        cmd = [str(self.rclone_bin), "--config", str(self.config_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def list_zip_files(self, folder_path_or_id: str) -> List[Dict[str, str]]:
        """Lista archivos .zip usando `rclone lsjson`."""
        target = f"{self.remote_name}:{folder_path_or_id}"
        out = self._run_cmd(["lsjson", target, "--include", "*.zip"])
        files = json.loads(out) if out else []
        return [{"id": f["Path"], "name": f["Name"]} for f in files]

    def download_file(self, remote_file_path: str, local_destination: Path):
        """Descarga un archivo remoto a la máquina local."""
        source = f"{self.remote_name}:{remote_file_path}"
        self._run_cmd(["copyto", source, str(local_destination)])

    def upload_file(self, local_file_path: Path, remote_folder: str, mime_type: Optional[str] = None):
        """Sube un archivo procesado al destino remoto."""
        if mime_type is None:
            mime_type = self._detect_mime_type(local_file_path)

        target = (f"{self.remote_name}:{remote_folder}/{local_file_path.name}")
        args = ["copyto", str(local_file_path), target]

        if mime_type:
            args.extend(["--drive-content-type", mime_type])

        self._run_cmd(args)
