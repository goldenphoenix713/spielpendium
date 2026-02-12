import sqlite3
import traceback
from typing import TYPE_CHECKING, Any

from config import DB_DIR, DB_FILE
from util.database.scripts import SQLScripts

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from os import PathLike
    from typing import Literal

__author__ = "Eduardo Ruiz"

__all__ = ["create", "SqliteDB"]


class SqliteDB:
    def __init__(self) -> None:
        self.database: PathLike[str] = DB_DIR / DB_FILE
        self.isolation_level: (
            Literal["DEFERRED", "EXCLUSIVE", "IMMEDIATE"] | None
        ) = None
        self.ignore_exc: bool = False
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def __enter__(self) -> sqlite3.Cursor:
        try:
            self.connection = sqlite3.connect(
                database=self.database, isolation_level=self.isolation_level
            )
            self.cursor = self.connection.cursor()
            return self.cursor
        except Exception as ex:
            traceback.print_exc()
            raise ex

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection is None or self.cursor is None:
            self.connection = None
            self.cursor = None
            return
        try:
            if exc_type is not None:
                self.connection.rollback()
            else:
                self.connection.commit()
        except Exception as ex:
            traceback.print_exc()
            raise ex
        finally:
            self.cursor.close()
            self.connection.close()
            self.connection = None
            self.cursor = None


def create() -> Any:
    with SqliteDB() as connection:
        connection.execute(SQLScripts.create_database)  # type:ignore[arg-type]


if __name__ == "__main__":
    my_successes = create()
    print(my_successes)
