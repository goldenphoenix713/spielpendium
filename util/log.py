import sys

from loguru import logger

from config import DEBUG, LOG_FILE


def set_up_logger() -> None:
    logger.remove()

    logger.add(
        sys.stderr,
        level="DEBUG" if DEBUG else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{line}</cyan> "
            "| <level>{message}</level>"
        ),
    )

    logger.add(
        f"{LOG_FILE}",
        rotation="1 day",
        compression="zip",
        level="DEBUG" if DEBUG else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{line}</cyan> "
            "| <level>{message}</level>"
        ),
    )


set_up_logger()
