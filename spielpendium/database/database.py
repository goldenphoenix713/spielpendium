import functools
from typing import List, Any

from PyQt5 import QtSql

from spielpendium import log
from spielpendium.constants import DB_FILE, DB_DIR
from spielpendium.database.scripts import SQLScripts

__author__ = 'Eduardo Ruiz'

__all__ = ['connect', 'disconnect', 'query', 'query_batch',
           'database_connection', 'create']


def connect() -> bool:
    """Open the database file connection.

    :return: True if the connection to the database was established,
        False otherwise
    """
    db = QtSql.QSqlDatabase.database()
    if not db.isValid():
        db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(str(DB_FILE))

    DB_DIR.mkdir(exist_ok=True)

    return db.open()


def disconnect():
    """Close the database file connection."""

    db = QtSql.QSqlDatabase.database()
    db.close()

    del db

    QtSql.QSqlDatabase.removeDatabase(
        QtSql.QSqlDatabase.database().connectionName()
    )


def database_connection(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        connect()
        ret = func(*args, **kwargs)
        disconnect()

        return ret
    return wrapper


def create() -> Any:
    return query_batch(SQLScripts.create_database)


@log.log(log.logger)
@database_connection
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
    else:
        return success


@log.log(log.logger)
@database_connection
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
    my_successes = create()
    print(my_successes)
