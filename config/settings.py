import os
from pathlib import Path


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = BASE_DIR / "config"
BIN_DIR = BASE_DIR / "bin"
CREDENTIALS_DIR = BASE_DIR / "credentials"

RCLONE_CONF_FILE = CONFIG_DIR / "rclone.conf"

STORAGE_DIR = BASE_DIR / "storage"
LOCAL_TEMP_DIR = STORAGE_DIR / "temp_extracted"
LOCAL_OUTPUT_DIR = STORAGE_DIR / "output_processed"
LOG_DIR = STORAGE_DIR / "logs"


# ============================================================
# EJECUCIÓN
# ============================================================

ENV_MODE = os.getenv(
    "ENV_MODE",
    "LOCAL",
).upper()

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()


# ============================================================
# RCLONE
# ============================================================

RCLONE_REMOTE = os.getenv(
    "RCLONE_REMOTE",
    "remote_drive",
)


# ============================================================
# IDIOMAS
# ============================================================

SOURCE_LANG = os.getenv(
    "SOURCE_LANG",
    "es",
)

TARGET_LANG = os.getenv(
    "TARGET_LANG",
    "en",
)


# ============================================================
# WHISPER / STT
# ============================================================

WHISPER_MODEL = os.getenv(
    "WHISPER_MODEL",
    "small",
)

WHISPER_DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
)

WHISPER_COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
)

WHISPER_BEAM_SIZE = int(
    os.getenv(
        "WHISPER_BEAM_SIZE",
        "5",
    )
)

WHISPER_VAD_FILTER = os.getenv(
    "WHISPER_VAD_FILTER",
    "true",
).lower() == "true"


# ============================================================
# EXTRACCIÓN DE ZIP
# ============================================================

# Profundidad máxima de ZIP dentro de ZIP.
#
# ZIP principal       -> nivel 0
# ZIP interno         -> nivel 1
# ZIP interno         -> nivel 2
# ...
MAX_ZIP_DEPTH = int(
    os.getenv(
        "MAX_ZIP_DEPTH",
        "3",
    )
)

# Número máximo de archivos que se pueden extraer.
MAX_EXTRACTED_FILES = int(
    os.getenv(
        "MAX_EXTRACTED_FILES",
        "10000",
    )
)

# Tamaño total máximo descomprimido.
#
# 50 GB por defecto.
MAX_EXTRACTED_SIZE_GB = float(
    os.getenv(
        "MAX_EXTRACTED_SIZE_GB",
        "50",
    )
)

MAX_EXTRACTED_SIZE_BYTES = int(
    MAX_EXTRACTED_SIZE_GB * 1024 * 1024 * 1024
)


# ============================================================
# ARCHIVOS SOPORTADOS
# ============================================================

VIDEO_EXTENSIONS = {
    ".mp4",
}


# ============================================================
# MIME TYPES
# ============================================================

MIME_MP4 = "video/mp4"
MIME_VTT = "text/vtt"
MIME_ZIP = "application/zip"


# ============================================================
# DIRECTORIOS
# ============================================================

def ensure_directories() -> None:
    """
    Crea los directorios necesarios para la ejecución.

    No se ejecuta automáticamente al importar este módulo.
    """
    directories = [
        CREDENTIALS_DIR,
        BIN_DIR,
        LOCAL_TEMP_DIR,
        LOCAL_OUTPUT_DIR,
        LOG_DIR,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )