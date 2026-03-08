# Spielpendium — Setup Guide

## Prerequisites

- **Python 3.11** (see `.python-version`)
- **[uv](https://docs.astral.sh/uv/)** — the project's package manager

Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/goldenphoenix713/spielpendium.git
cd spielpendium
```

---

## 2. Install Dependencies

```bash
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies
declared in `pyproject.toml`.

---

## 3. Configure Environment Variables

Copy the example below into a `.env` file at the project root:

```ini
# .env

# Your BoardGameGeek username (used to sync your collection)
TEST_USER=your_bgg_username

# Path to the SQLite database file
DB_FILE=db/spielpendium.sqlite

# Set to true to wipe and recreate the database on startup (use with care)
RESET_DB=false

# Enable Dash debug mode (hot reload, debug toolbar)
DEBUG=false

# BGG API token (REQUIRED — obtain from boardgamegeek.com/applications)
# See docs/BGG_API.md for full instructions.
BGG_API_TOKEN=your_token_here

# API retry settings
MAX_API_CHECKS=10
TIME_BETWEEN_API_CHECKS=5
```

All settings are defined in `config/settings.py` and loaded via
`pydantic-settings`.

---

## 4. Run the App

```bash
uv run python app.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

On first run, the app will create the database and sync your BGG collection
(this may take a minute depending on collection size and BGG API response times).

---

## 5. Running Tests

```bash
uv run pytest                                        # all tests
uv run pytest tests/test_collection.py -v            # single file
uv run pytest --cov=. --cov-report=term-missing      # with coverage
```

Tests use an in-memory SQLite database and never touch your real `DB_FILE`.

---

## 6. Pre-commit Hooks

Install the hooks (one-time):

```bash
uv run pre-commit install
```

Run manually against all files:

```bash
uv run pre-commit run --all-files
```

Hooks run in this order: yaml/toml/json checks → `ruff` lint → `ruff` format
→ `mypy` type check → `pytest` → `ty` check.

> **Tip:** If mypy crashes with `KeyError: 'setter_type'`, clear its cache:
> `rm -rf .mypy_cache`

---

## Common Issues

| Problem | Fix |
|---|---|
| `uv` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| BGG API returns 403 / no data | `BGG_API_TOKEN` is missing or invalid — see `docs/BGG_API.md` |
| BGG API returns 202 repeatedly | BGG is generating data — wait and retry |
| BGG API returns 429 | Rate limited — the app retries automatically |
| Database looks stale | Set `RESET_DB=true` in `.env` and restart |
| `VIRTUAL_ENV` warning from mypy | Harmless — mypy still uses the correct `.venv` |
