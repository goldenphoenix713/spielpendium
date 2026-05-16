import os
from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]

LOG_DIR = ROOT_DIR / "log"
LOG_FILE = LOG_DIR / "spielpendium.log"

# Allow overriding DB_FILE via environment variable for CI/testing
_env_db = os.getenv("DB_FILE")
if _env_db:
    DB_FILE = Path(_env_db)
    DB_DIR = DB_FILE.parent
else:
    DB_DIR = ROOT_DIR / "db"
    DB_FILE = DB_DIR / "spielpendium.sqlite"

DB_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_DIR = ROOT_DIR / "assets/images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
