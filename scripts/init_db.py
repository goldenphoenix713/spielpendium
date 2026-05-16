import sys
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parents[1]))

from util.models import create_db_and_tables


def main() -> None:
    print("Initializing database...")
    create_db_and_tables()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
