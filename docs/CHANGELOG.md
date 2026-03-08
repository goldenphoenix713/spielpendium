# Changelog

All notable changes to Spielpendium are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- Type annotations across all test files (`tests/test_game_details.py`, `tests/test_bgg_collection.py`, etc.) for improved developer experience and catch potential test-logic bugs
- Expanded test coverage for `api/bgg_api/game_details.py`, `api/bgg_api/collection.py`, and `util/models.py`
- `save_game_data_to_db` in `api/bgg_api/game_details.py` to allow saving single games rather than only bulk collections
- Related game badges and clickable navigation elements in the `open_modal` UI (`pages/collection.py`)

### Fixed
- CI workflow warning: removed unsupported `coverage_xml` input from `tj-actions/coverage-badge-py@v2`

### Changed
- Database schema: `Game.complexity` is now optional (`float | None`) to gracefully handle BGG accessories/promos that lack weight ratings
- Updated `open_modal` to correctly display "Weight: N/A" for games without a complexity rating and properly refresh the SQLAlchemy session for newly fetched games

## [0.7.0] — 2026-03-07 — API Refactor & Type Safety

### Added
- `api/bgg_api/` structure: split monolithic interface into functional modules:
  - `client.py` — base HTTP and XML parsing
  - `game_details.py` — game-specific ingestion logic
  - `images.py` — image processing and filesystem storage
  - `collection.py` — BGG collection retrieval

### Changed
- Replaced monolithic `api/bgg_api_interface.py` with `api/bgg_api/` package
- Updated all imports in `pages/collection.py`, `tests/test_bgg_ingestion.py`, and `tests/test_utils.py`

### Fixed
- Argument type mismatch in `Game` model instantiation within `game_details.py`
- Removed unused attributes (`thumbnail`, `users_rated`) previously incorrectly assigned to `Game` model

## [0.6.0] — 2026-03-06 — Housekeeping

### Changed
- Renamed `.geminiignore` → `.aiignore` for tool-agnostic coverage

---

## [0.5.0] — 2026-03-06 — Project Documentation

### Added
- `AGENTS.md` — AI coding assistant guide covering architecture, conventions,
  testing patterns, and pre-commit workflow
- `CHANGELOG.md` (this file) with history back to project start
- `DECISIONS.md` — architecture decision records (7 ADRs) explaining key
  design choices and what not to refactor

### Changed
- `README.md` — added Documentation table, `uv run` prefixes, `ty` mention,
  separate test-running section
- `SUMMARY.md` — corrected date to 2026, documented new test files and `ty`

---

## [0.4.0] — 2026-03-06 — Test Coverage Expansion

### Added
- `tests/test_collection.py` — full callback coverage for `update_grid` and
  `open_modal` (happy paths, empty collection, missing game, rating display,
  related games, owned-badge logic)
- `tests/test_connection_check.py` — tests for BGG connectivity helpers
- `tests/test_models_extra.py` — edge-case coverage for SQLModel models
- `tests/test_utils.py` — expanded coverage for `util/images.py` helpers

### Fixed
- Moved `Game` import into `TYPE_CHECKING` block in `test_collection.py`
  to satisfy ruff rule **TC001**

---

## [0.3.0] — 2026-03-05 — Pre-commit & Quality Pipeline

### Added
- Pre-commit hooks: `ruff-check`, `ruff-format`, `mypy`, `pytest`, `ty check`
- `pytest` configured in `pyproject.toml` (`pythonpath`, `testpaths`,
  `norecursedirs`)
- `ty` as a secondary type checker (skipped in CI)
- Dev dependencies: `pytest-cov`, `ty`, type stubs for `requests`, `xmltodict`,
  `pandas`, `openpyxl`, etc.

### Changed
- All source files updated to pass `mypy --strict`

---

## [0.2.0] — 2026-03 — UI: Collection Grid & Detail Modal

### Added
- `pages/collection.py` — `update_grid` callback renders game cards in a
  `dmc.SimpleGrid`; `open_modal` callback opens a detail modal on card click
- Game detail modal: high-res image, BGG rating, description, designers,
  publishers, related games with ownership badge
- `util/images.py` — binary image encode/decode helpers for BLOB storage

### Changed
- `pages/home.py` — basic home/landing page

---

## [0.1.0] — 2026-03 — Foundation

### Added
- `util/models.py` — full SQLModel schema: `Game`, `Collection`,
  `CollectionItem`, `RelatedGame`, `Person`, `Category`, `Publisher`,
  `OwnershipStatus`, `GameRelationship`, and all link tables
- `api/bgg_api_interface.py` — BGG XML ingestion with batch fetching
  (20 games/request) and `_process_and_save_game_details`
- `api/connection_check.py` — connectivity helpers
- `app.py` — Dash app entry point with `dmc.AppShell` and sidebar navigation
- `config/` — `pydantic-settings` config with `.env` support
- `util/log.py` — `loguru` logger setup
- Initial `README.md`, `SUMMARY.md`, `TASKS.md`
