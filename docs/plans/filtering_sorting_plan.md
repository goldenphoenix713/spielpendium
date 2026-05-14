# Plan: Collection Filtering & Sorting System

**Status:** Approved — Ready for Implementation  
**Created:** 2026-05-13  
**Author:** Antigravity + Eduardo Ruiz

---

## Decisions Made

| Question | Decision |
| --- | --- |
| Sidebar position | Move the **nav links to the header**; the left sidebar will be dedicated to filters. |
| Filter persistence | **Persist filter state** using `dcc.Store` with `storage_type="local"`. Users can clear via the "Clear All" button. |
| Ownership default | **Owned only** by default. Show a warning near the ownership filter that selecting "All" may be slow unless other filters are also active. |
| Result count | **Yes** — display "Showing X of Y games" in the **top-right** above the game grid. |
| Mobile behavior | **Drawer with a hamburger button**. Simple, familiar, and well-understood. |

---

## Architecture

### Layout Changes

The `app.py` `AppShell` will be restructured:

- **Header:** Add nav links (Collection, Statistics, Settings) alongside the existing Spielpendium title. The nav moves here from the navbar.
- **Navbar (left sidebar):** Repurposed entirely for filters and the sort selector.
- **Main area:** Game grid with result count in the top-right. On mobile, a hamburger button opens the filter sidebar as a `dmc.Drawer`.

### Data Flow

```text
Page Load
  └─> update_collection_store() [new callback]
        └─> Fetches all owned games from DB
        └─> Serializes to JSON-safe list of dicts
        └─> Stores in dcc.Store("collection-store", storage_type="local")

Filter/Sort Change
  └─> update_grid() [updated callback]
        └─> Reads dcc.Store("collection-store")
        └─> Reads all filter/sort controls as State/Input
        └─> Filters and sorts in-memory (no DB hit)
        └─> Returns updated grid + "Showing X of Y games" count
```

> **Note:** `dcc.Store` data will be a list of plain dicts (not SQLModel objects, which aren't JSON-serializable). A helper function `game_to_dict()` will serialize the relevant fields.

---

## Sorting

A `dmc.Select` at the **top of the sidebar**, followed by a `dmc.SegmentedControl` for ascending/descending direction.

| Sort Field | DB Field | Default Dir | Priority |
| --- | --- | --- | --- |
| **Name** | `game.name` | Asc | ⭐⭐⭐ Default |
| **BGG Rating** | `game.bgg_rating` | Desc | ⭐⭐⭐ |
| **BGG Rank** | `game.bgg_rank` | Asc | ⭐⭐⭐ |
| **Year Released** | `game.release_year` | Desc | ⭐⭐⭐ |
| **Complexity** | `game.complexity` | Asc | ⭐⭐ |
| **Play Time** | `game.min_play_time` | Asc | ⭐⭐ |

**Implementation note:** Fields that are nullable (`bgg_rank`, `bgg_rating`, `complexity`) must always sort `None` values to the end regardless of direction, using a key like `(value is None, value)`.

---

## Filters

All filters are `AND`-ed together. Within a multi-select filter (categories, etc.), logic is `OR`.

### Tier 1 — Essential (implement first)

#### 1. Player Count

- **Data Fields:** `min_players`, `max_players`
- **Filter Type:** Range (integer)
- **Component:** `dmc.RangeSlider` — min=1, max=dynamically set from collection
- **Logic:** Show games where `min_players ≤ selected_max AND max_players ≥ selected_min`
- **Priority:** ⭐⭐⭐

#### 2. Complexity (Weight)

- **Data Field:** `game.complexity` (1.0–5.0)
- **Filter Type:** Range (float)
- **Component:** `dmc.RangeSlider` — min=1.0, max=5.0, step=0.1
- **Logic:** Show games where `min ≤ complexity ≤ max`. Games with `complexity = None` are hidden when filter is active.
- **Priority:** ⭐⭐⭐

#### 3. Play Time

- **Data Fields:** `min_play_time`, `max_play_time`
- **Filter Type:** Range (integer, in minutes)
- **Component:** `dmc.RangeSlider` — min=0, max=240+ (cap at 240, meaning "240+"), step=15. Add a `dmc.ChipGroup` for quick-filters: "< 30 min", "30–60 min", "60–120 min", "120+ min".
- **Logic:** Show games where `min_play_time ≤ selected_max AND max_play_time ≥ selected_min`
- **Priority:** ⭐⭐⭐

#### 4. BGG Rating

- **Data Field:** `game.bgg_rating` (1.0–10.0)
- **Filter Type:** Range (float)
- **Component:** `dmc.RangeSlider` — min=1.0, max=10.0, step=0.1
- **Logic:** Show games where `min ≤ bgg_rating ≤ max`. Games with `bgg_rating = None` excluded when active.
- **Priority:** ⭐⭐⭐

#### 5. Category

- **Data Field:** `game.categories` (many-to-many)
- **Filter Type:** Multi-select categorical (OR within)
- **Component:** `dmc.MultiSelect` — searchable, dynamically populated from collection
- **Logic:** Show games with **at least one** selected category.
- **Priority:** ⭐⭐⭐
- **Note:** Limit to categories appearing in at least 2 games in the collection to reduce noise.

#### 6. Name Search

- **Data Field:** `game.name`
- **Filter Type:** Text search (substring)
- **Component:** `dmc.TextInput` with search icon, `debounce=True`
- **Logic:** Show games where `query.lower() in game.name.lower()`
- **Priority:** ⭐⭐⭐ — Essential once collection exceeds ~50 games.

---

### Tier 2 — High Value (implement second)

#### 7. Ownership Status

- **Data Field:** `CollectionItem.ownership_status.name`
- **Filter Type:** Categorical, multi-select toggle
- **Component:** `dmc.ChipGroup` (multi=True) with chips: "Owned", "Prev. Owned", "Want to Buy"
- **Default:** Owned only.
- **Warning:** Display a `dmc.Alert` when user selects "All" without other active filters, noting it may load a large number of games.
- **Priority:** ⭐⭐
- **Note:** Requires changing the initial data load to fetch all statuses, not just `own=True`.

#### 8. Year Released

- **Data Field:** `game.release_year`
- **Filter Type:** Range (integer)
- **Component:** `dmc.RangeSlider` — min=dynamically set, max=current year, step=1
- **Priority:** ⭐⭐

#### 9. BGG Rank

- **Data Field:** `game.bgg_rank`
- **Filter Type:** Single upper bound
- **Component:** `dmc.NumberInput` ("Show only games ranked better than: ___") or `dmc.Slider`
- **Logic:** Show games where `bgg_rank ≤ threshold`. Games with `bgg_rank = None` excluded when active.
- **Priority:** ⭐⭐

#### 10. Minimum Age

- **Data Field:** `game.min_age`
- **Filter Type:** Single upper bound (show games suitable *up to* a given age)
- **Component:** `dmc.Select` with options: "Any", "6+", "8+", "10+", "12+", "14+", "18+"
- **Logic:** Show games where `min_age ≤ selected_max_age`
- **Priority:** ⭐ (niche but clear use case for families)

---

### Tier 3 — Nice to Have (implement later)

#### 11. Designer / Author

- **Data Field:** `game.authors` (many-to-many)
- **Filter Type:** Multi-select with search
- **Component:** `dmc.MultiSelect` — searchable, dynamically populated
- **Priority:** ⭐ (niche, but very useful for fans of specific designers)

#### 12. Publisher

- **Data Field:** `game.publishers` (many-to-many)
- **Filter Type:** Multi-select with search
- **Component:** `dmc.MultiSelect` — searchable, dynamically populated
- **Priority:** ⭐ (most useful for large collections)

---

## UI Component Summary

| Component | Purpose |
| --- | --- |
| `dmc.Select` | Sort-by dropdown |
| `dmc.SegmentedControl` | Ascending / Descending toggle |
| `dmc.RangeSlider` | Player count, complexity, play time, rating, year |
| `dmc.Slider` | BGG rank upper bound |
| `dmc.ChipGroup` | Ownership status toggles, play time quick-filters |
| `dmc.MultiSelect` | Categories, designers, publishers (searchable) |
| `dmc.TextInput` | Name search (debounced) |
| `dmc.NumberInput` | BGG rank threshold |
| `dmc.Select` | Minimum age |
| `dmc.Button` | "Clear All Filters" |
| `dmc.Alert` | Warning for "all ownership statuses" selection |
| `dmc.Drawer` | Mobile filter panel (opened by hamburger button) |
| `dmc.Divider` | Visual separation between filter groups |
| `dcc.Store` (local) | Persisted filter state + full collection data |

---

## New Callbacks

| Callback | Trigger | Output |
| --- | --- | --- |
| `update_collection_store()` | Page load | `dcc.Store("collection-store")` |
| `update_grid()` (updated) | Any filter/sort change | Grid children + result count text |
| `clear_filters()` (new) | "Clear All" button | Reset all filter controls to defaults |
| `toggle_mobile_drawer()` (new) | Hamburger button | `dmc.Drawer` opened state |

---

## Recommended Implementation Order

1. Restructure `app.py` — move nav to header, sidebar for filters.
2. Add `collection-store` (`dcc.Store`) and `update_collection_store()` callback.
3. Add sort selector + direction toggle; update `update_grid()` to use store.
4. Add name search text input.
5. Add player count, complexity, play time, and rating sliders.
6. Add category multi-select (requires dynamic population).
7. Add result count display ("Showing X of Y games").
8. Add ownership status chips + warning (requires loading all statuses in store).
9. Add year, rank, and age filters.
10. Add mobile drawer + hamburger button in header.
11. Implement `dcc.Store` filter state persistence.
12. Add designer and publisher filters.
