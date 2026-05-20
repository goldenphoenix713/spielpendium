# Changelog

All notable changes to Spielpendium are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

## [1.0.0] — 2026-05-19 — Production Release & Mobile Optimization

### Added

- **Dynamic Image Persistence**: Implemented automated, self-healing symbolic
  link creation in `config/directories.py` to route the `assets/images` folder
  directly into the persistent Render DB volume, preventing game images from
  being lost across container redeploys.
- **Mobile Responsive Sizing**: Overrode Mantine modal styling with a custom
  `.responsive-detail-modal` layout that expands to 96% width on screens
  under 768px and wraps button groups and titles cleanly.
- **Auto-Stacking Grid layout**: Upgraded the details modal to stack key
  information and columns vertically on mobile screens while maintaining
  side-by-side structures on desktop viewports.
- **Horizontal Table Scrolling**: Integrated smooth swipe-to-scroll features
  for the collection list-view table using `.responsive-table-card` CSS
  wrappers, keeping all columns aligned and beautiful without breaking
  structural unit test assertions.
- **Responsive Game Title Truncation**: Added native CSS ellipsis truncation
  (`.list-title-text`) on the list-view to automatically shorten extremely
  long board game titles on narrow/mobile screens while maintaining the full
  title for desktops.
- **Mobile Statistics Optimization**: Made the statistics page dashboard fully
  responsive by implementing grid span breakpoints (`cols={"base": 1, "xs":
  2, "md": 4}`) and dynamic left margins in Plotly figures to automatically
  make category and designer text highly readable on phones.
- **WSGI Server Exponentiation**: Hoisted the `dash_app` and `server` variables
  in `app.py` to global scope, resolving Gunicorn binding crashes during Render
  builds.

## [0.9.1] — 2026-05-17 — Dynamic Settings & Auto-Refresh Integration

### Added

- **Auto-Refresh Setting Implementation**: Fully implemented `auto_refresh`
  support on collection page load (`pages/collection.py`). If enabled in user
  settings, the application automatically initiates a BGG collection refresh
  in a background thread upon entering the page.
- **Unit Tests**: Added robust test coverage for `auto_refresh` in
  `tests/test_final_gaps.py` (`test_start_sync_auto_refresh`) and dynamic
  paging limits in `tests/test_collection.py` (`test_dynamic_page_size`).

### Fixed

- **Hardcoded Page Size**: Replaced the static `PAGE_SIZE = 50` constant in
  the collection view with a dynamic look-up to the user settings database,
  ensuring changes in user preferences instantly reflect in the rendered card
  count and pagination calculations.

## [0.9.0] — 2026-05-16 — Statistics, Onboarding & Multi-User Architecture

### Added

- **Statistics Dashboard** (`pages/statistics.py`): Comprehensive analytics for
  collection complexity, player counts, categories, and ownership breakdown
  using interactive Plotly charts.
- **Onboarding Flow** (`pages/home.py`): Premium first-visit experience that
  guides new users to connect their BoardGameGeek account.
- **Multi-User Local Architecture**: Migrated active user tracking to
  `dcc.Store` with `local` storage. This allows multiple users on the same app
  instance to maintain private sessions and avoids leaking database-level
  active profiles to new visitors.
- **Unit Tests**: Added `tests/test_statistics.py` and significantly updated
  `tests/test_pages.py` to cover the new dynamic layout logic.

### Fixed

- **CI Test Stability**: Resolved `OperationalError` and `PageError` during
  test collection by mocking database settings and Dash page registration.
- **Game Card Titles**: Implemented a CSS-based marquee effect for long game
  titles, ensuring readability without sacrificing layout integrity.
- **Badge Positioning**: Moved ownership and rating badges to a separate line
  to prevent title overflow on cards.

### Changed

- **Home Page**: Transformed from a static placeholder to a dynamic dashboard
  that adapts based on the user's local connection status.
- **Collection Rendering**: Improved empty-state guidance with specific alerts
  for uninitialized users.

## [0.8.0] — 2026-03-08 — CI Fixes & Test Enhancements

### Added

- Type annotations across all test files (`tests/test_game_details.py`,
  `tests/test_bgg_collection.py`, etc.) for improved developer experience and
  to catch potential test-logic bugs.
- Expanded test coverage for `api/bgg_api/game_details.py`,
  `api/bgg_api/collection.py`, and `util/models.py`.
- `save_game_data_to_db` in `api/bgg_api/game_details.py` to allow saving
  single games rather than only bulk collections.
- Related game badges and clickable navigation elements in the `open_modal`
  UI (`pages/collection.py`).

### Fixed

- CI workflow warning: removed unsupported `coverage_xml` input from
  `tj-actions/coverage-badge-py@v2`.

### Changed

- Database schema: `Game.complexity` is now optional (`float | None`) to
  gracefully handle BGG accessories/promos that lack weight ratings.
- Updated `open_modal` to correctly display "Weight: N/A" for games without a
  complexity rating and properly refresh the SQLAlchemy session for newly
  fetched games.

## [0.7.0] — 2026-03-07 — API Refactor & Type Safety

### Added

- `api/bgg_api/` structure: split monolithic interface into functional
  modules:
  - `client.py` — base HTTP and XML parsing
  - `game_details.py` — game-specific ingestion logic
  - `images.py` — image processing and filesystem storage
  - `collection.py` — BGG collection retrieval

### Changed

- Replaced monolithic `api/bgg_api_interface.py` with `api/bgg_api/` package.
- Updated all imports in `pages/collection.py`, `tests/test_bgg_ingestion.py`,
  and `tests/test_utils.py`.

### Fixed

- Argument type mismatch in `Game` model instantiation within `game_details.py`.
- Removed unused attributes (`thumbnail`, `users_rated`) previously
  incorrectly assigned to `Game` model.

## [0.6.0] — 2026-03-06 — Housekeeping

### Changed

- Renamed `.geminiignore` → `.aiignore` for tool-agnostic coverage.

---

## [0.5.0] — 2026-03-06 — Project Documentation

### Added

- `AGENTS.md` — AI coding assistant guide covering architecture, conventions,
  testing patterns, and pre-commit workflow.
- `CHANGELOG.md` (this file) with history back to project start.
- `DECISIONS.md` — architecture decision records (7 ADRs) explaining key
  design choices and what not to refactor.

### Changed

- `README.md` — added Documentation table, `uv run` prefixes, `ty` mention,
  separate test-running section.
- `SUMMARY.md` — corrected date to 2026, documented new test files and `ty`.

---

## [0.4.0] — 2026-03-06 — Test Coverage Expansion

### Added

- `tests/test_collection.py` — full callback coverage for `update_grid` and
  `open_modal` (happy paths, empty collection, missing game, rating display,
  related games, owned-badge logic).
- `tests/test_connection_check.py` — tests for BGG connectivity helpers.
- `tests/test_models_extra.py` — edge-case coverage for SQLModel models.
- `tests/test_utils.py` — expanded coverage for `util/images.py` helpers.

### Fixed

- Moved `Game` import into `TYPE_CHECKING` block in `test_collection.py` to
  satisfy ruff rule **TC001**.

---

## [0.3.0] — 2026-03-05 — Pre-commit & Quality Pipeline

### Added

- Pre-commit hooks: `ruff-check`, `ruff-format`, `mypy`, `pytest`, `ty check`.
- `pytest` configured in `pyproject.toml` (`pythonpath`, `testpaths`,
  `norecursedirs`).
- `ty` as a secondary type checker (skipped in CI).
- Dev dependencies: `pytest-cov`, `ty`, type stubs for `requests`, `xmltodict`,
  `pandas`, `openpyxl`, etc.

### Changed

- All source files updated to pass `mypy --strict`.

---

## [0.2.0] — 2026-03 — UI: Collection Grid & Detail Modal

### Added

- `pages/collection.py` — `update_grid` callback renders game cards in a
  `dmc.SimpleGrid`; `open_modal` callback opens a detail modal on card click.
- Game detail modal: high-res image, BGG rating, description, designers,
  publishers, related games with ownership badge.
- `util/images.py` — binary image encode/decode helpers for BLOB storage.

### Changed

- `pages/home.py` — basic home/landing page.

---

## [0.1.0] — 2026-03 — Foundation

### Added

- `util/models.py` — full SQLModel schema: `Game`, `Collection`,
  `CollectionItem`, `RelatedGame`, `Person`, `Category`, `Publisher`,
  `OwnershipStatus`, `GameRelationship`, and all link tables.
- `api/bgg_api_interface.py` — BGG XML ingestion with batch fetching (20
  games/request) and `_process_and_save_game_details`.
- `api/connection_check.py` — connectivity helpers.
- `app.py` — Dash app entry point with `dmc.AppShell` and sidebar navigation.
- `config/` — `pydantic-settings` config with `.env` support.
- `util/log.py` — `loguru` logger setup.
- Initial `README.md`, `SUMMARY.md`, `TASKS.md`.
