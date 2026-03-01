from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]

LOG_DIR = ROOT_DIR / "log"
LOG_FILE = LOG_DIR / "spielpendium.log"

DB_DIR = ROOT_DIR / "db"
DB_FILE = DB_DIR / "spielpendium.sqlite"
