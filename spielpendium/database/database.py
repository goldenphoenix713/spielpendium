import functools
from typing import List, Any
import os

from PyQt5 import QtSql

from spielpendium import log
from spielpendium.constants import DB_FILE
from spielpendium.database.scripts import SQLScripts

__all__ = ['connect', 'disconnect', 'query', 'query_batch',
           'database_connection', 'create']


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
    QtSql.QSqlDatabase.removeDatabase(db.databaseName())


def database_connection(db_file):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            connect(db_file)
            ret = func(*args, **kwargs)
            disconnect()

            return ret
        return wrapper
    return decorator


def create():
    query_batch(SQLScripts.create_database)


@log.log(log.logger)
@database_connection(DB_FILE)
def query(command: str, params: List = None) -> Any:
    if params is None:
        params = []

    log.logger.debug('Preparing query for execution.')
    q = QtSql.QSqlQuery()

    q.prepare(command)

    for param in params:
        q.addBindValue(param)

    log.logger.debug('Executing the query.')
    success = q.exec()

    if not success:
        raise IOError(f'Unable to execute the command "{command}" '
                      f'with the parameters "{params}". '
                      f'Reason: {q.lastError().text()}.')

    if q.isSelect():
        ret = []

        log.logger.debug('Getting selected data.')
        while q.next():
            for ii in range(len(params)):
                ret.append(q.value(ii))

        return ret

    return success


@log.log(log.logger)
@database_connection(DB_FILE)
def query_batch(commands: tuple) -> list:
    log.logger.debug(f'Number of commands in batch: {len(commands)}')
    q = QtSql.QSqlQuery()

    successes = [True for _ in range(len(commands))]

    for ii, command in enumerate(commands):
        if command.strip() != '':
            log.logger.debug(f'Running query {ii+1} of {len(commands)}:\n'
                             f'{command.strip()}')

            if not q.exec(command):
                successes[ii] = False
                log.logger.error(f'Command could not be run:\n    {command}. '
                                 f'Reason:\n    {q.lastError().text()}')
            else:
                log.logger.debug('Success.')

    return successes


if __name__ == '__main__':
    create()
