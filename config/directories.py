import contextlib
import os
import shutil
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

# Define the persistent images folder inside DB_DIR
PERSISTENT_IMAGE_DIR = DB_DIR / "images"
PERSISTENT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_DIR = ROOT_DIR / "assets/images"

# Ensure assets/images is a symlink to the persistent image folder
try:
    if not IMAGE_DIR.is_symlink():
        if IMAGE_DIR.exists():
            # If it's a real directory, migrate any existing images to the persistent dir
            for item in IMAGE_DIR.iterdir():
                dest = PERSISTENT_IMAGE_DIR / item.name
                if not dest.exists():
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
            # Remove the local folder so we can replace it with a symlink
            shutil.rmtree(IMAGE_DIR)
            with contextlib.suppress(FileExistsError):
                os.symlink(
                    PERSISTENT_IMAGE_DIR, IMAGE_DIR, target_is_directory=True
                )
        else:
            # Create parent directory assets/ if it doesn't exist
            IMAGE_DIR.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.suppress(FileExistsError):
                os.symlink(
                    PERSISTENT_IMAGE_DIR, IMAGE_DIR, target_is_directory=True
                )
except Exception:
    # Fallback to standard directory if symlink fails (e.g. windows without permissions or CI/test environment)
    with contextlib.suppress(FileExistsError):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
