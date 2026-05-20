# Spielpendium - The Board Game Compendium

**Official Website**: [www.spielpendium.com](https://www.spielpendium.com)

![Coverage](./coverage.svg)
[![CI](https://github.com/goldenphoenix713/spielpendium/actions/workflows/ci.yml/badge.svg?branch=restructure)](https://github.com/goldenphoenix713/spielpendium/actions/workflows/ci.yml)

Spielpendium allows users to create a compendium of their board games. A user
can create their list by searching through BoardGameGeek's online catalog and
adding games. Additionally, if a user has a collection on BoardGameGeek, they
can import that list.

The name is a portmanteau of "spiel" (German for "game", a reference to
Germany's centrality in the board game sphere) and "compendium".

## Features

- **Deep Collection Insights**: Visualize your library through interactive
  charts. Analyze complexity distributions, player count support, and category
  breakdowns.
- **Guided Onboarding**: Seamless first-visit experience that helps new users
  connect their BGG account and initialize their local dashboard.
- **Import from BGG**: Seamlessly import your existing BoardGameGeek collection.
- **Detailed Game Information**: View comprehensive details including
  high-resolution images, descriptions, complexities, player counts,
  designers, and publishers.
- **Collection Management**: Organize and visualize your board games in a
  beautiful, interactive card grid.
- **Associated Games Tracking**: Track expansions, accessories, and
  reimplementations. Easily see what items from a board game family are already
  in your collection.

## Technology Stack

Spielpendium is built using modern Python web technologies:

- **Frontend**: Dash, Dash Mantine Components, Dash Iconify
- **Backend**: Python 3.11+, SQLModel (SQLAlchemy & Pydantic), SQLite

## Setup and Installation

1. Ensure you have Python 3.11+ installed.
2. Install `uv` if you haven't already:
   `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Clone the repository and navigate into the directory.
4. Install dependencies:

   ```bash
   uv sync
   ```

5. Create a `.env` file at the project root (see `docs/SETUP.md` for all options).
   At minimum you need:

   ```ini
   TEST_USER=your_bgg_username
   BGG_API_TOKEN=your_token_here   # Required — see docs/BGG_API.md
   DB_FILE=db/spielpendium.sqlite
   ```

6. Initialize the database:

   ```bash
   uv run python scripts/init_db.py
   ```

7. Run the application:

   ```bash
   uv run python app.py
   ```

> **BGG API Token:** The BGG XML API now requires an Application Token sent
> as a `Bearer` token in the `Authorization` header. Obtain one at
> [boardgamegeek.com/applications](https://boardgamegeek.com/applications).
> See [`docs/BGG_API.md`](docs/BGG_API.md) for full details.

## Documentation

| File | Purpose |
| :--- | :--- |
| [`docs/SETUP.md`](docs/SETUP.md) | Full setup and installation guide |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture and data flow |
| [`docs/BGG_API.md`](docs/BGG_API.md) | BGG API token, rate limits, and terms of use |
| [`docs/TASKS.md`](docs/TASKS.md) | Phase-by-phase feature task list |
| [`docs/SUMMARY.md`](docs/SUMMARY.md) | High-level project status overview |
| [`docs/AGENTS.md`](docs/AGENTS.md) | Guide for AI coding assistants |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decision records (read before refactoring) |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Per-session change log |

## Development

- Code quality is maintained with `ruff` for linting and formatting.
- Type checking is enforced with strict `mypy` and `ty` settings.
- Pre-commit hooks run ruff, mypy, ty, and pytest automatically on every commit.
- A `pytest` suite covers BGG ingestion, UI callbacks, models, and utilities.

### Environment Setup

Create a `.env` file in the root directory. See [`docs/SETUP.md`](docs/SETUP.md)
for all available options, and [`docs/BGG_API.md`](docs/BGG_API.md) for
instructions on obtaining a BGG API token.

### Formatting, Linting and Type Checking

```bash
uv run ruff check . --fix
uv run ruff format .
uv run mypy .
uv run ty check
```

### Running Tests

```bash
uv run pytest
uv run pytest --cov=. --cov-report=term-missing
```
