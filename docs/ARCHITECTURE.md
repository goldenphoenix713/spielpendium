# Spielpendium — Architecture

## Overview

Spielpendium is a single-user, local-first Dash web application. It syncs a
user's BoardGameGeek (BGG) collection once (or on demand), stores everything
in a local SQLite database, and serves a card-based UI for browsing games and
their details.

---

## High-Level Data Flow

```
┌──────────────────────────────────────────────┐
│              BoardGameGeek API               │
│   (XML via HTTPS, xmlapi2/ — token required) │
└──────────────────┬───────────────────────────┘
                   │  HTTP GET (XML) + Authorization: Bearer <token>
                   ▼
┌──────────────────────────────────────────────┐
│         api/bgg_api_interface.py             │
│                                              │
│  1. get_xml_info()   — fetch + retry logic   │
│  2. xmltodict.parse() — XML → Python dict    │
│  3. _process_and_save_game_details()         │
│     — map dict fields → SQLModel objects     │
│  4. save_collection_data_to_db()             │
│     — write Collection + CollectionItems     │
└──────────────────┬───────────────────────────┘
                   │  SQLModel Session
                   ▼
┌──────────────────────────────────────────────┐
│         SQLite Database (db/*.sqlite)        │
│         ORM models in util/models.py         │
└──────────────────┬───────────────────────────┘
                   │  SQLModel select()
                   ▼
┌──────────────────────────────────────────────┐
│          Dash Application (app.py)           │
│                                              │
│  pages/home.py        — welcome/landing      │
│  pages/collection.py  — game grid + modal   │
│  callbacks/           — shared callbacks     │
└──────────────────────────────────────────────┘
                   │  HTTP (browser)
                   ▼
              User's Browser
```

---

## Module Responsibilities

### `app.py`
Entry point. Calls `create_db_and_tables()` on startup, then builds and
returns the `Dash` app with the `MantineProvider` + `AppShell` layout.

### `api/bgg_api_interface.py`
All BGG communication. Key public functions:

| Function | Purpose |
|---|---|
| `get_user_game_collection()` | Top-level: check DB first, fetch from BGG if absent |
| `save_collection_data_to_db()` | Batch-fetch game details, persist Collection + items |
| `get_game_info()` | Fetch game details XML for one or more `bgg_id`s |
| `get_single_image()` | Download image bytes from CDN (no auth header) |
| `search_bgg()` | Search BGG by title |

All requests to the BGG XML API include an `Authorization: Bearer <token>` header
from `BGG_API_TOKEN`. Image CDN requests (`get_single_image()`) intentionally
omit this header as they hit a different domain. Retry logic handles BGG's
202 (data generating) and 429 (rate limited) responses automatically.

See `docs/BGG_API.md` for full API documentation, including how to obtain a token.

### `util/models.py`
SQLModel ORM definitions. All database schema lives here. Also exports the
module-level `engine` connected to `config.DB_FILE`.

### `config/settings.py`
`pydantic-settings` model. Reads from `.env`. Exports named constants
(`BGG_API_TOKEN`, `DB_FILE`, `RESET_DB`, etc.) for import throughout the app.

### `pages/collection.py`
The main page. Renders the game card grid and the game detail modal.
Callbacks in this file query the DB directly via `Session(engine)`.

### `util/images.py`
Tiny helper: converts raw image bytes → base64 `data:image/jpeg;base64,…`
URI for embedding in the browser.

### `util/log.py`
Configures `loguru` with console + file sinks based on `config.DEBUG` and
`config.LOG_FILE`.

---

## Database Schema

All primary keys are 16-byte binary UUIDs (`BinaryUUIDField`).
Look up games by `bgg_id` (int, unique), not by internal UUID.

```
Game ──< RelatedGame >── Game          self-referential via GameRelationship.type
Game ──< PersonGameLink >── Person     role discriminated by PersonRole (author/artist)
Game ──< PublisherGameLink >── Publisher
Game ──< GameCategoryLink >── Category
Game ──< CollectionItem >── Collection
CollectionItem ── OwnershipStatus      (owned / want / prevowned)
```

**Key relationships:**

- `RelatedGame.source_game_id` → the expansion/variant
- `RelatedGame.target_game_id` → the base game
- `Collection.username` identifies the BGG user

---

## Request Lifecycle (Collection Load)

```
Browser (page load)
  └─► Dash callback: update_grid(username)
        ├─ get_user_game_collection(username)
        │     ├─ DB hit? → return Collection from SQLite
        │     └─ Miss:
        │           ├─ GET /xmlapi2/collection?username=…  [Authorization: Bearer …]
        │           ├─ save_collection_data_to_db()
        │           │     ├─ batch GET /xmlapi2/thing?id=…&stats=1
        │           │     ├─ _process_and_save_game_details() × N games
        │           │     └─ session.commit()
        │           └─ return Collection from SQLite
        └─ render game card grid (dmc.SimpleGrid of Card components)
```

---

## Configuration Flow

```
.env file
  └─► pydantic-settings (config/settings.py)
        └─► module-level constants (DB_FILE, DEBUG, etc.)
              ├─► util/models.py  (engine path)
              ├─► util/log.py     (log level / file)
              └─► api/bgg_api_interface.py  (API URL, token, retry settings)
```

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Language | Python 3.11, strict mypy |
| Web framework | Dash 4.x (multi-page) |
| UI components | dash-mantine-components 2.x (dark-mode-first) |
| Database | SQLite via SQLModel + SQLAlchemy 2 |
| BGG client | HTTP + `xmltodict` (raw XML parsing) |
| Images | Stored as binary blobs in SQLite, served as base64 URIs |
| Config | `pydantic-settings` + `.env` |
| Logging | `loguru` |
| Package manager | `uv` |
| Linting/formatting | `ruff` |
| Type checking | `mypy --strict` + `ty` |
| Testing | `pytest` (in-memory SQLite fixtures) |
