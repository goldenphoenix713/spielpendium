from spielpendium import database
from spielpendium.constants import DB_FILE


@database.database_connection(DB_FILE)
def create_database():
    script_path = f'{database.SCRIPT_DIRECTORY}create_database.sql'
    database.run_script(script_path)


if __name__ == '__main__':
    create_database()
