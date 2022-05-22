from spielpendium import database


def create_database():
    script_path = f'{database.SCRIPT_DIRECTORY}create_database.sql'
    database.run_script(script_path)


if __name__ == '__main__':
    from spielpendium.constants import DB_FILE

    database.connect(DB_FILE)
    create_database()
    database.disconnect()
