from pathlib import Path

IMAGE_SIZE = 64

ROOT_DIR = Path(__file__).parents[1].absolute()

PROGRAM_NAME = ROOT_DIR.name

LOG_DIR = ROOT_DIR / 'log'
DB_DIR = ROOT_DIR / 'db'

LOG_FILE = LOG_DIR / f'{PROGRAM_NAME}.log'
DB_FILE = DB_DIR / f'{PROGRAM_NAME}.sqlite'
