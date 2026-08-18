import sys
import os
import platform
import zipfile
import shutil
from pathlib import Path
import requests

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
RCLONE_EXE = BIN_DIR / ("rclone.exe" if platform.system() == "Windows" else "rclone")

def ensure_rclone_binary() -> Path:
    """Garantiza la presencia del binario portable de Rclone en ./bin/ sin instalar nada en el SO."""
    if RCLONE_EXE.exists():
        return RCLONE_EXE

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    arch = "amd64" # Ajustar a arm64 si aplica
    
    os_name = "windows" if system == "windows" else "linux"
    url = f"https://downloads.rclone.org/rclone-current-{os_name}-{arch}.zip"
    zip_path = BIN_DIR / "rclone.zip"

    print(f"[RCLONE] Descargando binario portable de Rclone desde {url}...")
    response = requests.get(url, stream=True)
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if member.endswith("rclone") or member.endswith("rclone.exe"):
                with z.open(member) as src, open(RCLONE_EXE, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                break

    zip_path.unlink()
    if system != "windows":
        RCLONE_EXE.chmod(0o755)

    print(f"[RCLONE] Binario portable instalado en: {RCLONE_EXE}")
    return RCLONE_EXE