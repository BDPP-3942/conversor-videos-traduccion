import json
import mimetypes
import subprocess

from pathlib import Path
from typing import List, Dict, Optional

from config import settings
from src.rclone_installer import ensure_rclone_binary


class CloudManager:
    """
    Abstracción de las operaciones de almacenamiento remoto mediante rclone.
    """

    def __init__(
        self,
        remote_name: Optional[str] = None,
    ):
        self.rclone_bin = ensure_rclone_binary()

        self.config_path = settings.RCLONE_CONF_FILE

        self.remote_name = (
            remote_name
            or settings.RCLONE_REMOTE
        )

    # ========================================================
    # COMANDOS
    # ========================================================

    def _run_cmd(
        self,
        args: List[str],
    ) -> str:
        cmd = [
            str(self.rclone_bin),
            "--config",
            str(self.config_path),
        ]

        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

        except subprocess.CalledProcessError as exc:
            stderr = (
                exc.stderr.strip()
                if exc.stderr
                else "Unknown rclone error"
            )

            raise RuntimeError(
                f"rclone command failed: {stderr}"
            ) from exc

        return result.stdout

    # ========================================================
    # LISTAR
    # ========================================================

    def list_zip_files(
        self,
        folder_path_or_id: str,
    ) -> List[Dict[str, str]]:
        """
        Lista los ZIP existentes directamente dentro
        de la carpeta remota.
        """

        target = (
            f"{self.remote_name}:"
            f"{folder_path_or_id}"
        )

        output = self._run_cmd(
            [
                "lsjson",
                target,
                "--include",
                "*.zip",
            ]
        )

        files = (
            json.loads(output)
            if output
            else []
        )

        return [
            {
                "id": file["Path"],
                "name": file["Name"],
            }
            for file in files
            if not file.get("IsDir", False)
        ]

    # ========================================================
    # DESCARGAR
    # ========================================================

    def download_file(
        self,
        remote_file_path: str,
        local_destination: Path,
    ) -> None:
        """
        Descarga un archivo desde el remoto.
        """

        source = (
            f"{self.remote_name}:"
            f"{remote_file_path}"
        )

        local_destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._run_cmd(
            [
                "copyto",
                source,
                str(local_destination),
            ]
        )

    # ========================================================
    # SUBIR
    # ========================================================

    def upload_file(
        self,
        local_file_path: Path,
        remote_folder: str,
        mime_type: Optional[str] = None,
    ) -> None:
        """
        Sube un archivo al remoto.

        Si mime_type no se especifica, se intenta inferir
        mediante la extensión del archivo.
        """

        if not local_file_path.exists():
            raise FileNotFoundError(
                f"Local file does not exist: "
                f"{local_file_path}"
            )

        if mime_type is None:
            mime_type = self._detect_mime_type(
                local_file_path
            )

        target = (
            f"{self.remote_name}:"
            f"{remote_folder}/"
            f"{local_file_path.name}"
        )

        args = [
            "copyto",
            str(local_file_path),
            target,
        ]

        if mime_type:
            args.extend(
                [
                    "--metadata-set",
                    f"content-type={mime_type}",
                ]
            )

        self._run_cmd(args)

    # ========================================================
    # MOVER
    # ========================================================

    def move_file(
        self,
        remote_file_path: str,
        destination_folder: str,
    ) -> None:
        """
        Mueve un archivo dentro del mismo remoto.
        """

        source = (
            f"{self.remote_name}:"
            f"{remote_file_path}"
        )

        destination = (
            f"{self.remote_name}:"
            f"{destination_folder}"
        )

        self._run_cmd(
            [
                "moveto",
                source,
                (
                    f"{destination}/"
                    f"{Path(remote_file_path).name}"
                ),
            ]
        )

    # ========================================================
    # MIME
    # ========================================================

    @staticmethod
    def _detect_mime_type(
        file_path: Path,
    ) -> Optional[str]:
        mime_type, _ = mimetypes.guess_type(
            file_path.name
        )

        return mime_type
