from typing import List, Any
import os

from PyQt5 import QtSql


def connect(db_file: str) -> bool:
    """Open the database file connection.

    :param db_file: The filename for the SQLite database.
    :return: True if the connection to the database was established,
        False otherwise
    """
    db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(db_file)

    db_dir = os.path.dirname(db_file)

    if not os.path.exists(db_dir):
        os.mkdir(db_dir)

    return db.open()


def disconnect():
    """Close the database file connection."""

    db = QtSql.QSqlDatabase.database()
    db.close()
    db.removeDatabase(db.databaseName())


def create_tables():
    ...


def _create_games_table():
    ...


def query(command: str, params: List) -> Any:
    q = QtSql.QSqlQuery()

    q.prepare(command)

    for param in params:
        q.addBindValue(param)

    success = q.exec()

    if not success:
        raise IOError(f'Unable to execute the command "{command}"'
                      f'with the parameters "{params}".')

    ret = []

    if q.isSelect():
        while q.next():
            for ii in range(len(params)):
                ret.append(q.value(ii))

        return ret

    return success


if __name__ == '__main__':
    pass
