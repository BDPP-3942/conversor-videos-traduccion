import os
from pathlib import Path

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
BIN_DIR = BASE_DIR / "bin"
CREDENTIALS_DIR = BASE_DIR / "credentials"

# Ubicación del archivo de configuración de Rclone
RCLONE_CONF_FILE = CONFIG_DIR / "rclone.conf"

# Modo de ejecución ('LOCAL' guarda copia en disco, 'PRODUCTION' usa carpetas volátiles)
ENV_MODE = os.getenv("ENV_MODE", "LOCAL").upper()

# Configuración de Whisper STT (Exclusivo CPU)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# Idiomas del pipeline
SOURCE_LANG = "es"
TARGET_LANG = "en"

# Almacenamiento local (Utilizado únicamente en modo LOCAL)
STORAGE_DIR = BASE_DIR / "storage"
LOCAL_TEMP_DIR = STORAGE_DIR / "temp_extracted"
LOCAL_OUTPUT_DIR = STORAGE_DIR / "output_processed"

# Creación de directorios base
for d in [CREDENTIALS_DIR, BIN_DIR, LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)