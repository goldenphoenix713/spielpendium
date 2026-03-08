# Architecture Decision Records (ADRs)

This document records the key technical decisions made in Spielpendium and the
reasoning behind them. Before refactoring or changing any of these choices,
read the relevant entry here first.

---

## ADR-001: Binary UUID Primary Keys

**Decision:** All SQLModel tables use 16-byte binary UUIDs as primary keys,
stored as `BINARY(16)` blobs via the custom `BinaryUUIDField` helper.

**Why:**
- SQLite lacks a native UUID type; `BINARY(16)` is compact (vs. 36-char text).
- UUIDs allow records to be created client-side without a round-trip to the DB
  to retrieve an auto-increment ID.
- Consistent with potential future migration to a UUID-native database.

**Trade-offs:**
- Binary PKs are opaque in SQL queries / DB browser tools. Use `bgg_id` (int)
  as the human-readable game identifier in application logic.
- All FK references must also use `BinaryUUIDField`; do not mix with integers.

**Do not change to:** integer auto-increment PKs without updating every FK
column and all test fixtures.

---

## ADR-002: `bgg_id` as the Application-Level Game Identifier

**Decision:** `Game.bgg_id` (int, unique, indexed) is used throughout the
application to look up games — e.g., in Dash callbacks, modal triggers, and
API calls. The internal binary UUID `id` is only used for FK joins.

**Why:**
- BGG IDs are stable, well-known, and map 1-to-1 with BGG's own API.
- Avoids exposing opaque binary blobs in Dash component IDs (`pattern-matching
  callbacks use `{"index": bgg_id, "type": "game-card"}`).
- Simplifies debugging — you can look up any game on BGG directly by its ID.

**Do not change to:** using the UUID `id` in callback pattern-matching or UI
state without a strong reason.

---

## ADR-003: SQLite + SQLModel (not Postgres or raw SQL)

**Decision:** The database is a local SQLite file managed via SQLModel
(SQLAlchemy 2 ORM). File path is configured via `DB_FILE` in `.env`.

**Why:**
- Single-user, local-first application — no need for a server-based DB.
- SQLModel gives type-safe model definitions that double as Pydantic models.
- SQLite requires zero infrastructure; easy to reset (`RESET_DB=true`).

**Trade-offs:**
- No concurrent writes; not suitable for multi-user deployment without
  switching engines (SQLModel/SQLAlchemy make this relatively easy).
- Binary BLOB storage (images) inflates the DB file; this is acceptable for
  a personal collection.

---

## ADR-004: Local Filesystem Image Caching

**Decision:** Game thumbnail and full-resolution images are downloaded and stored
as files directly in the local `assets/images` directory, and the DB only stores
the relative filename string (`Game.image_path`).

**Why:**
- Avoids inflating the SQLite database to massive unmanageable sizes when syncing
  large collections or high-res images.
- Images can be served natively by Dash's static asset router (`/assets/images/...`)
  without requiring manual base64 binary encoding/decoding on the fly.
- Still enables fully offline browsing of the collection once data is synced.

**Trade-offs:**
- Deleting the `db/` folder doesn't clean up disk space; the `assets/images` folder
  must be managed separately if wiping state.

**Do not change to:** storing hotlinked BGG URLs. BGG's CDN has strict
hotlinking limits and this application is intended to work offline.

---

## ADR-005: Dash + dash-mantine-components (not Flask/FastAPI + React)

**Decision:** The web UI is built with Plotly Dash 4.x and
`dash-mantine-components` (DMC) 2.x, using multi-page routing
(`dash.register_page`).

**Why:**
- Dash allows a pure-Python application with no JavaScript build step.
- DMC provides a rich, dark-mode-first Mantine component library.
- Multi-page routing via `dash.register_page` avoids a custom router.

**Trade-offs:**
- Dash's callback model is less flexible than React for complex interactions;
  some patterns (e.g., clicking related games to navigate) require careful
  use of `dcc.Store` or URL state.
- `dash.*` and `dmc.*` have no type stubs; mypy overrides
  `ignore_missing_imports = true` for these modules.

**Important:** Always mock `dash.register_page` before importing any `pages/`
module in tests (see `AGENTS.md` → Testing).

---

## ADR-006: `from __future__ import annotations` + `TYPE_CHECKING` Imports

**Decision:** Every source file begins with `from __future__ import annotations`.
Imports used only for type hints are placed inside `if TYPE_CHECKING:` blocks.

**Why:**
- Required by ruff rule **TC001** to avoid circular imports at runtime.
- Enables forward references (e.g., `"Game"` in Relationship definitions)
  without string quoting.
- Consistent with strict mypy + ruff configuration.

**Do not skip** the `TYPE_CHECKING` guard for type-only imports; ruff will
fail the pre-commit hook.

---

## ADR-007: `uv` as the Package and Task Runner

**Decision:** `uv` is used for dependency management and running all dev tools
(`uv run pytest`, `uv run mypy .`, `uv run pre-commit`, etc.).

**Why:**
- Fast installs and lockfile management.
- `uv run` ensures tools execute inside the project's virtual environment
  without activating it manually.

**Do not use:** bare `python`, `pip`, or `pip install` for project tooling.
Always prefix with `uv run` or activate `.venv` explicitly.
