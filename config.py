import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


APP_NAME = os.getenv("APP_NAME", "spielpendium")

BGG_API_TOKEN = os.getenv("BGG_API_TOKEN", "")
BGG_API_URL = os.getenv("BGG_API_URL", "https://www.boardgamegeek.com/xmlapi/")
MAX_API_CHECKS = int(os.getenv("MAX_API_CHECKS", "10"))
TIME_BETWEEN_API_CHECKS = int(os.getenv("TIME_BETWEEN_API_CHECKS", "5"))

IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "64"))

ROOT_DIR = Path(__file__).parent

DEBUG = os.getenv("DEBUG", False)
LOG_DIR = ROOT_DIR / os.getenv("LOG_DIR", "log")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    logging.BASIC_FORMAT,
)

DB_DIR = ROOT_DIR / os.getenv("DB_DIR", "db")

LOG_FILE = LOG_DIR / os.getenv("LOG_FILE", "log.log")
DB_FILE = DB_DIR / os.getenv("DB_FILE", "sqlite.db")
