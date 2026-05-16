# Spielpendium — AI Agent Guide

This document is the primary reference for any AI coding assistant (Copilot,
Gemini, Claude, etc.) working in this repository. Read it fully before making
any changes.

---

## Project Overview

**Spielpendium** is a Python web application that lets a user browse their
BoardGameGeek (BGG) board-game collection through a card-based UI. Clicking a
game card opens a detail modal with ratings, descriptions, designers, and a
list of related games (expansions, reimplementations) with ownership badges.

**Stack:**

| Layer | Technology |
| :--- | :--- |
| Language | Python 3.11 (strict type checking) |
| Web framework | [Dash](https://dash.plotly.com/) 4.x with multi-page routing |
| UI components | `dash-mantine-components` (DMC) 2.x — dark-mode-first |
| Database | SQLite via [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy 2 |
| BGG API client | `bgg-api` library + raw XML parsing (`xmltodict`, `lxml`) |
| Config | `pydantic-settings` + `.env` file |
| Logging | `loguru` |
| Package manager | `uv` (use `uv run` for all tool invocations) |

---

## Repository Layout

```text
spielpendium/
├── api/
│   ├── bgg_api/               # BGG data ingestion package
│   └── connection_check.py    # Connectivity helpers
├── callbacks/                 # Shared / global Dash callbacks
├── config/
│   ├── settings.py            # pydantic-settings Config model
│   └── directories.py        # Path constants (DB_FILE, etc.)
├── docs/
│   ├── AGENTS.md              # (this file) AI coding assistant guide
│   ├── ARCHITECTURE.md        # System architecture and data flow
│   ├── BGG_API.md             # BGG API token, rate limits, terms of use
│   ├── CHANGELOG.md           # Per-session change log
│   ├── DECISIONS.md           # Architecture decision records
│   ├── SETUP.md               # Local development setup guide
│   ├── SUMMARY.md             # High-level project status
│   └── TASKS.md               # Phase-by-phase feature task list
├── pages/
│   ├── home.py                # Home page
│   └── collection.py         # Collection grid + detail modal
├── util/
│   ├── models.py              # SQLModel ORM models (source of truth for schema)
│   └── log.py                 # Loguru setup
├── tests/                     # All pytest tests (see Testing section)
├── app.py                     # Dash app entry point — run this to start
├── pyproject.toml             # All tool configuration lives here
└── README.md                  # Project overview
```

> **`old/`** — legacy scripts, do not touch or import from them.
>
> **Before refactoring** any core design (PKs, image storage, UI framework,
> etc.), read `docs/DECISIONS.md` first. Many choices that look "improvable" are
> deliberate — the rationale is documented there.

---

## Database Schema (SQLModel)

All models live in `util/models.py`. Primary keys are 16-byte binary UUIDs
(`BinaryUUIDField`). The central model is `Game`.

```text
Game ──< RelatedGame >── Game          (self-referential: expansions, etc.)
Game ──< PersonGameLink >── Person     (authors / artists via PersonRole)
Game ──< PublisherGameLink >── Publisher
Game ──< GameCategoryLink >── Category
Game ──< CollectionItem >── Collection (user ownership)
CollectionItem ── OwnershipStatus
```

Key points:

- `Game.bgg_id` (int, unique, indexed) is the BGG canonical identifier.
  **Always look up games by `bgg_id`**, not the internal UUID.
- `RelatedGame.source_game_id` → the game that *is* the expansion/variant;
  `target_game_id` → the base game.
- `util/models.py` exports a module-level `engine` connected to `DB_FILE`.
  Import it as `from util.models import engine`.

---

## Configuration

Settings are loaded via `config/settings.py` (`pydantic-settings`). Values are
read from a `.env` file at the project root. Key variables:

| Variable | Purpose |
| :--- | :--- |
| `BGG_API_TOKEN` | **Required.** Bearer token for the BGG XML API. Get one at [boardgamegeek.com/applications](https://boardgamegeek.com/applications). See `docs/BGG_API.md`. |
| `TEST_USER` | BGG account to sync collection for |
| `DB_FILE` | Path to the SQLite database file |
| `RESET_DB` | If `true`, wipe and recreate the DB on startup |
| `DEBUG` | Dash debug mode |

Import config constants directly: `from config import DB_FILE, RESET_DB`.

---

## Code Conventions

### Type Hints (strict)

- Every function must have fully annotated parameters and return types.
- Use `from __future__ import annotations` at the top of every file.
- Runtime-only imports go in the top-level block; type-only imports go inside
  `if TYPE_CHECKING:` to satisfy ruff rule **TC001**.
- `mypy --strict` must pass. Do not use `Any` unless absolutely necessary and
  comment why.

### Formatting & Linting (ruff)

- Line length: **79 characters**.
- Quote style: **double quotes**.
- Import order: stdlib → third-party → local, sorted by ruff/isort.
- Run `uv run ruff check --fix .` and `uv run ruff format .` before committing.

### Naming

- Classes: `PascalCase`. Functions/variables: `snake_case`.
- Dash callback output variables: descriptive, e.g. `grid`, `loading`, `opened`.
- Pytest fixtures: use `name=` kwarg (e.g. `@pytest.fixture(name="session")`).

### Dash Callbacks

- Always check `dash.callback_context.triggered` before reading trigger data.
- Return early with a sensible default (closed modal, alert, `False` loading)
  when there is nothing to do.
- Callbacks that query the DB open their own `Session(engine)` context manager;
  do **not** keep sessions open across callbacks.

---

## Testing

```text
tests/
├── test_models.py              # Core model creation helpers (create_mock_game)
├── test_models_extra.py        # Additional model edge-case coverage
├── test_bgg_ingestion.py       # BGG XML parsing + DB ingestion
├── test_ui_components.py       # Dash component rendering
├── test_collection.py          # update_grid + open_modal callbacks
├── test_connection_check.py    # API connectivity checks
└── test_utils.py               # api/bgg_api/images.py + misc helpers
```

**Running tests:**

```bash
uv run pytest                   # all tests
uv run pytest tests/test_collection.py -v   # single file
uv run pytest --cov=. --cov-report=term-missing   # with coverage
```

**Writing new tests:**

- Use `create_mock_game(bgg_id, name)` from `tests/test_models.py` for `Game`
  fixtures.
- For DB-dependent tests, use `mem_engine` + `session` fixtures (in-memory
  SQLite) — never touch the real database file.
- Patch `pages.collection.engine` when testing callbacks that open DB sessions.
- Patch `dash.register_page` before importing any `pages/` module:

  ```python
  import dash
  dash.register_page = MagicMock()
  from pages.collection import my_callback  # noqa: E402
  ```

---

## Pre-commit Hooks

All hooks are enforced on every commit. They run in this order:

1. `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`, `check-json`,
   `check-toml`, `detect-private-key`, `pretty-format-json`
2. **`ruff-check --fix`** — linting
3. **`ruff-format`** — formatting
4. **`mypy .`** — strict type checking (excludes `old/`, `test*`)
5. **`pytest`** — full test suite
6. **`ty check`** — additional type checker (skipped in CI)

If mypy crashes with `KeyError: 'setter_type'`, it is a cache corruption issue.
Fix it with: `rm -rf .mypy_cache`

Run hooks manually: `uv run pre-commit run --all-files`

---

## Adding New Features — Checklist

Before opening a PR or committing:

- [ ] All new functions/methods have complete type annotations
- [ ] `from __future__ import annotations` at the top of new files
- [ ] Type-only imports are inside `if TYPE_CHECKING:`
- [ ] Tests written for new logic (happy path + at least one error path)
- [ ] `uv run pre-commit run --all-files` passes cleanly
- [ ] `docs/TASKS.md` updated to reflect new status
- [ ] `docs/CHANGELOG.md` `[Unreleased]` section updated with a summary of changes

---

## Current Development Focus

See `docs/TASKS.md` for the authoritative task list. As of the latest commit:

- **Phase 4 (Game Detail View)** is in progress — Task 4.3 (related games with
  ownership badges) is the active work item.
- **Phase 5 (Navigation between related games)** is planned next.
- **Testing & QA** is ongoing; aim for broad coverage of all callback branches.
