from pydantic_settings import BaseSettings, SettingsConfigDict

from config import ROOT_DIR


class Settings(BaseSettings):
    app_name: str = "spielpendium"

    bgg_api_token: str = ""
    bgg_api_url: str = "https://boardgamegeek.com/xmlapi2/"
    max_api_checks: int = 10
    time_between_api_checks: int = 5

    image_size: int = 64

    debug: bool = False

    reset_db: bool = False

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", extra="ignore"
    )


settings = Settings()

APP_NAME = settings.app_name

BGG_API_TOKEN = settings.bgg_api_token
BGG_API_URL = settings.bgg_api_url
MAX_API_CHECKS = settings.max_api_checks
TIME_BETWEEN_API_CHECKS = settings.time_between_api_checks

IMAGE_SIZE = settings.image_size

DEBUG = settings.debug

RESET_DB = settings.reset_db
