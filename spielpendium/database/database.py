import functools
import pathlib
from typing import List, Any
import os

from PyQt5 import QtSql

from spielpendium import log
from spielpendium.constants import DB_FILE

__all__ = ['SCRIPT_DIRECTORY', 'connect', 'disconnect', 'run_script', 'query',
           'database_connection']

SCRIPT_DIRECTORY = (f'{pathlib.Path(__file__).parent.absolute()}'
                    f'{os.sep}scripts{os.sep}')


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


@log.log(log.logger)
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

    ret = []

    if q.isSelect():
        log.logger.debug('Getting selected data.')
        while q.next():
            for ii in range(len(params)):
                ret.append(q.value(ii))

        return ret

    return success


@database_connection(DB_FILE)
def run_script(script_file):
    q = QtSql.QSqlQuery()

    # Open and read the file as a single buffer
    log.logger.debug('Reading SQL file.')
    with open(script_file, 'r') as file:
        sql_file = file.read()

    log.logger.debug('Successfully read SQL file.')

    # all SQL commands (split on ';')
    sql_commands = sql_file.split(';')

    # Execute every command from the input file
    for command in sql_commands:
        # This will skip and report errors
        # For example, if the tables do not yet exist, this will skip over
        # the DROP TABLE commands
        command = command.strip()

        if command != '':
            log.logger.debug(f'Running SQL command:\n    {command}')
            if not q.exec(command):
                log.logger.exception(f'Command skipped:\n    {command}')

    log.logger.debug('Finished running commands.')
