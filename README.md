# Spielpendium - The Board Game Compendium

Spielpendium allows users to create a compendium of their board games. A user can create their list by searching through BoardGameGeek's online catalog and adding games. Additionally, if a user has a collection on BoardGameGeek, they can import that list.

The name is a portmanteau of "spiel" (German for "game", a reference to Germany's centrality in the board game sphere) and "compendium".

## Features

- **Import from BGG**: Seamlessly import your existing BoardGameGeek collection.
- **Detailed Game Information**: View comprehensive details including high-resolution images, descriptions, complexities, player counts, designers, and publishers.
- **Collection Management**: Organize and visualize your board games in a beautiful, interactive card grid.
- **Associated Games Tracking**: Track expansions, accessories, and reimplementations. Easily see what items from a board game family are already in your collection.

## Technology Stack

Spielpendium is built using modern Python web technologies:

- **Frontend**: Dash, Dash Mantine Components, Dash Iconify
- **Backend**: Python 3.11+, SQLModel (SQLAlchemy & Pydantic), SQLite

## Setup and Installation

1. Ensure you have Python 3.11+ installed.
2. Install `uv` if you haven't already: `pip install uv`
3. Clone the repository and navigate into the directory.
4. Create and sync the virtual environment using `uv`:
   ```bash
   uv sync
   ```
5. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
6. Run the application:
   ```bash
   python app.py
   ```

## Development

- Code quality is maintained with `ruff` for linting and formatting.
- Type checking is enforced with strict `mypy` settings.
- Pre-commit hooks are configured to ensure code guidelines are met before pushing.
- A `pytest` suite is included for testing the BGG ingestion and data processing pipelines.

### Environment Setup

Create a `.env` file in the root directory (you can use the provided template if available) to configure the application, such as setting the database path.

### Formatting and Linting
```bash
ruff check . --fix
ruff format .
mypy .
```
