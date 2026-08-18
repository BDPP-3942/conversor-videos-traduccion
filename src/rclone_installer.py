import platform
import shutil
import zipfile

from pathlib import Path

import requests

from config import settings


def _get_rclone_filename() -> str:
    """
    Devuelve el nombre esperado del binario.
    """

    if platform.system() == "Windows":
        return "rclone.exe"

    return "rclone"


def _get_rclone_download_url() -> str:
    """
    Construye la URL de descarga según el sistema.
    """

    system = platform.system().lower()

    machine = platform.machine().lower()

    if system == "windows":
        os_name = "windows"
    elif system == "linux":
        os_name = "linux"
    else:
        raise RuntimeError(
            "Unsupported operating system: "
            f"{platform.system()}"
        )

    if machine in (
        "x86_64",
        "amd64",
    ):
        architecture = "amd64"

    elif machine in (
        "aarch64",
        "arm64",
    ):
        architecture = "arm64"

    else:
        raise RuntimeError(
            "Unsupported architecture: "
            f"{machine}"
        )

    return (
        "https://downloads.rclone.org/"
        f"rclone-current-{os_name}-"
        f"{architecture}.zip"
    )


def ensure_rclone_binary() -> Path:
    """
    Garantiza que existe un binario portable de rclone.

    Para producción es recomendable incluir el binario
    previamente en ./bin/ y evitar la descarga automática.
    """

    binary_path = (
        settings.BIN_DIR
        / _get_rclone_filename()
    )

    if binary_path.exists():
        return binary_path

    settings.BIN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    url = _get_rclone_download_url()

    archive_path = (
        settings.BIN_DIR
        / "rclone_download.zip"
    )

    print(
        "[RCLONE] Downloading rclone from: "
        f"{url}"
    )

    try:
        response = requests.get(
            url,
            stream=True,
            timeout=60,
        )

        response.raise_for_status()

        with archive_path.open(
            "wb"
        ) as output:

            shutil.copyfileobj(
                response.raw,
                output,
            )

        with zipfile.ZipFile(
            archive_path,
            "r",
        ) as archive:

            matching_member = next(
                (
                    name
                    for name in archive.namelist()
                    if name.endswith(
                        _get_rclone_filename()
                    )
                ),
                None,
            )

            if not matching_member:
                raise RuntimeError(
                    "rclone binary not found "
                    "inside downloaded archive"
                )

            with archive.open(
                matching_member
            ) as source, binary_path.open(
                "wb"
            ) as destination:

                shutil.copyfileobj(
                    source,
                    destination,
                )

    finally:
        if archive_path.exists():
            archive_path.unlink()

    if platform.system() != "Windows":
        binary_path.chmod(0o755)

    print(
        "[RCLONE] Binary available at: "
        f"{binary_path}"
    )

    return binary_path