from pathlib import Path

__all__ = ["create_database"]

import log


def create_database() -> str:
    with open(Path(__file__).parent / "create_database.sql") as file:
        sql = file.read()

    log.logger.debug("Successfully read SQL file.")

    return sql
