from __future__ import annotations

from datetime import datetime
from typing import Any

import dash_mantine_components as dmc
from dash import Input, Output, State, callback, dcc
from dash_iconify import DashIconify

# ---------------------------------------------------------------------------
# Filter defaults
# ---------------------------------------------------------------------------
CURRENT_YEAR = datetime.now().year

FILTER_DEFAULTS: dict[str, Any] = {
    "name": "",
    "players": [1, 10],
    "play_time": [0, 300],
    "complexity": [1.0, 5.0],
    "bgg_rating": [1.0, 10.0],
    "bgg_rank_max": None,
    "year": [1970, CURRENT_YEAR],
    "categories": [],
    "sort_by": "name",
    "sort_dir": "asc",
}


# ---------------------------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------------------------


def generate_sidebar() -> dmc.Stack:
    """Returns the full sidebar containing sort controls and all filters."""
    return dmc.Stack(
        gap="lg",
        p="md",
        children=[
            dcc.Store(id="filters-store", storage_type="local"),
            # ── Sort ────────────────────────────────────────────────────────
            dmc.Divider(label="Sort", labelPosition="left"),
            dmc.Select(
                id="sort-by",
                label="Sort by",
                value=FILTER_DEFAULTS["sort_by"],
                data=[
                    {"label": "Name", "value": "name"},
                    {"label": "BGG Rating", "value": "bgg_rating"},
                    {"label": "BGG Rank", "value": "bgg_rank"},
                    {"label": "Year Released", "value": "release_year"},
                    {"label": "Complexity", "value": "complexity"},
                    {"label": "Play Time", "value": "min_play_time"},
                ],
                allowDeselect=False,
            ),
            dmc.SegmentedControl(
                id="sort-dir",
                value=FILTER_DEFAULTS["sort_dir"],
                data=[
                    {"label": "↑ Asc", "value": "asc"},
                    {"label": "↓ Desc", "value": "desc"},
                ],
                fullWidth=True,
            ),
            # ── Filters ─────────────────────────────────────────────────────
            dmc.Divider(
                label=dmc.Group(
                    [
                        dmc.Text("Filters", size="sm"),
                        dmc.Button(
                            "Clear All",
                            id="clear-filters-btn",
                            size="compact-xs",
                            variant="subtle",
                            color="gray",
                            rightSection=DashIconify(
                                icon="tabler:x", width=12
                            ),
                        ),
                    ],
                    gap="xs",
                ),
                labelPosition="left",
            ),
            dmc.TextInput(
                id="name-filter",
                label="Name",
                placeholder="Search…",
                value=FILTER_DEFAULTS["name"],
                debounce=True,
                leftSection=DashIconify(icon="tabler:search", width=16),
            ),
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text("Players", size="sm", fw=500),
                    dmc.RangeSlider(
                        id="players-filter",
                        min=1,
                        max=10,
                        step=1,
                        value=FILTER_DEFAULTS["players"],
                        marks=[
                            {"value": i, "label": str(i) if i % 2 == 0 else ""}
                            for i in range(1, 11)
                        ],
                        mb="xs",
                    ),
                ],
            ),
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text("Play Time (min)", size="sm", fw=500),
                    dmc.RangeSlider(
                        id="time-filter",
                        min=0,
                        max=300,
                        step=15,
                        value=FILTER_DEFAULTS["play_time"],
                        marks=[
                            {
                                "value": v,
                                "label": str(v) if v % 60 == 0 else "",
                            }
                            for v in range(0, 301, 15)
                        ],
                        mb="xs",
                    ),
                ],
            ),
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text("Complexity (Weight)", size="sm", fw=500),
                    dmc.RangeSlider(
                        id="complexity-filter",
                        min=1.0,
                        max=5.0,
                        step=0.25,
                        value=FILTER_DEFAULTS["complexity"],
                        marks=[
                            {"value": v, "label": str(v)}
                            for v in [1, 2, 3, 4, 5]
                        ],
                        mb="xs",
                    ),
                ],
            ),
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text("BGG Rating", size="sm", fw=500),
                    dmc.RangeSlider(
                        id="bgg-rating-filter",
                        min=1.0,
                        max=10.0,
                        step=0.1,
                        value=FILTER_DEFAULTS["bgg_rating"],
                        marks=[
                            {"value": v, "label": str(v)} for v in range(1, 11)
                        ],
                        mb="xs",
                    ),
                ],
            ),
            dmc.NumberInput(
                id="bgg-rank-filter",
                label="BGG Rank — better than",
                placeholder="Any rank",
                value=FILTER_DEFAULTS["bgg_rank_max"],
                min=1,
                allowDecimal=False,
            ),
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text("Year Released", size="sm", fw=500),
                    dmc.RangeSlider(
                        id="year-filter",
                        min=1970,
                        max=CURRENT_YEAR,
                        step=1,
                        value=FILTER_DEFAULTS["year"],
                        marks=[
                            {"value": v, "label": str(v)}
                            for v in range(1970, CURRENT_YEAR + 1, 10)
                        ],
                        mb="xs",
                    ),
                ],
            ),
            dmc.MultiSelect(
                id="category-filter",
                label="Categories",
                placeholder="All categories",
                value=FILTER_DEFAULTS["categories"],
                searchable=True,
                clearable=True,
                data=[],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Callback 1: populate filter bounds AND restore saved state from localStorage.
#
# Reads filters-store as STATE (not Input) to avoid a dependency cycle.
# The cycle would be:
#   collection-store → players-filter.value → filters-store → sort-by.value
#   → filters-store  (cycle!)
#
# By reading filters-store as State here, this callback is only triggered by
# collection-store changing, and filter changes only write to filters-store
# (via save_filter_state) without triggering this callback again.
# ---------------------------------------------------------------------------
@callback(
    Output("category-filter", "data"),
    Output("sort-by", "value"),
    Output("sort-dir", "value"),
    Output("name-filter", "value"),
    Output("players-filter", "max"),
    Output("players-filter", "value"),
    Output("time-filter", "max"),
    Output("time-filter", "value"),
    Output("complexity-filter", "value"),
    Output("bgg-rating-filter", "value"),
    Output("bgg-rank-filter", "value"),
    Output("year-filter", "min"),
    Output("year-filter", "value"),
    Output("category-filter", "value"),
    Input("collection-store", "data"),
    State("filters-store", "data"),
    prevent_initial_call=True,
)
def populate_filter_bounds(
    games: list[dict[str, Any]],
    saved: dict[str, Any] | None,
) -> tuple[
    list[dict[str, str]],
    str,
    str,
    str,
    int,
    list[int],
    int,
    list[int],
    list[float],
    list[float],
    int | None,
    int,
    list[int],
    list[str],
]:
    """Set slider bounds from the collection and restore any saved filter state."""
    sf = saved or {}

    if not games:
        return (
            [],
            sf.get("sort_by", FILTER_DEFAULTS["sort_by"]),
            sf.get("sort_dir", FILTER_DEFAULTS["sort_dir"]),
            sf.get("name", FILTER_DEFAULTS["name"]),
            10,
            sf.get("players", FILTER_DEFAULTS["players"]),
            300,
            sf.get("play_time", FILTER_DEFAULTS["play_time"]),
            sf.get("complexity", FILTER_DEFAULTS["complexity"]),
            sf.get("bgg_rating", FILTER_DEFAULTS["bgg_rating"]),
            sf.get("bgg_rank_max", FILTER_DEFAULTS["bgg_rank_max"]),
            1970,
            sf.get("year", FILTER_DEFAULTS["year"]),
            sf.get("categories", FILTER_DEFAULTS["categories"]),
        )

    all_categories = sorted({
        cat for game in games for cat in (game.get("categories") or [])
    })
    category_data = [{"label": c, "value": c} for c in all_categories]

    max_players = min(
        max((game.get("max_players") or 10 for game in games), default=10), 20
    )
    max_time = min(
        max((game.get("max_play_time") or 300 for game in games), default=300),
        360,
    )
    min_year = min(
        (game.get("release_year") or CURRENT_YEAR for game in games),
        default=1970,
    )

    return (
        category_data,
        sf.get("sort_by", FILTER_DEFAULTS["sort_by"]),
        sf.get("sort_dir", FILTER_DEFAULTS["sort_dir"]),
        sf.get("name", FILTER_DEFAULTS["name"]),
        max_players,
        sf.get("players", [1, max_players]),
        max_time,
        sf.get("play_time", [0, max_time]),
        sf.get("complexity", FILTER_DEFAULTS["complexity"]),
        sf.get("bgg_rating", FILTER_DEFAULTS["bgg_rating"]),
        sf.get("bgg_rank_max", FILTER_DEFAULTS["bgg_rank_max"]),
        min_year,
        sf.get("year", [min_year, CURRENT_YEAR]),
        sf.get("categories", FILTER_DEFAULTS["categories"]),
    )


# ---------------------------------------------------------------------------
# Callback 2: persist current filter state to localStorage
# ---------------------------------------------------------------------------
@callback(
    Output("filters-store", "data"),
    Input("sort-by", "value"),
    Input("sort-dir", "value"),
    Input("name-filter", "value"),
    Input("players-filter", "value"),
    Input("time-filter", "value"),
    Input("complexity-filter", "value"),
    Input("bgg-rating-filter", "value"),
    Input("bgg-rank-filter", "value"),
    Input("year-filter", "value"),
    Input("category-filter", "value"),
)
def save_filter_state(
    sort_by: str,
    sort_dir: str,
    name: str,
    players: list[int],
    play_time: list[int],
    complexity: list[float],
    bgg_rating: list[float],
    bgg_rank_max: int | None,
    year: list[int],
    categories: list[str],
) -> dict[str, Any]:
    """Persist all filter/sort state to localStorage."""
    return {
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "name": name,
        "players": players,
        "play_time": play_time,
        "complexity": complexity,
        "bgg_rating": bgg_rating,
        "bgg_rank_max": bgg_rank_max,
        "year": year,
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# Callback 3: clear all filters
# ---------------------------------------------------------------------------
@callback(
    Output("sort-by", "value", allow_duplicate=True),
    Output("sort-dir", "value", allow_duplicate=True),
    Output("name-filter", "value", allow_duplicate=True),
    Output("players-filter", "value", allow_duplicate=True),
    Output("time-filter", "value", allow_duplicate=True),
    Output("complexity-filter", "value", allow_duplicate=True),
    Output("bgg-rating-filter", "value", allow_duplicate=True),
    Output("bgg-rank-filter", "value", allow_duplicate=True),
    Output("year-filter", "value", allow_duplicate=True),
    Output("category-filter", "value", allow_duplicate=True),
    Input("clear-filters-btn", "n_clicks"),
    State("players-filter", "max"),
    State("time-filter", "max"),
    State("year-filter", "min"),
    prevent_initial_call=True,
)
def clear_filters(
    _: int | None,
    players_max: int,
    time_max: int,
    year_min: int,
) -> tuple[
    str,
    str,
    str,
    list[int],
    list[int],
    list[float],
    list[float],
    None,
    list[int],
    list[str],
]:
    """Reset all filters to defaults."""
    return (
        FILTER_DEFAULTS["sort_by"],
        FILTER_DEFAULTS["sort_dir"],
        FILTER_DEFAULTS["name"],
        [1, players_max],
        [0, time_max],
        FILTER_DEFAULTS["complexity"],
        FILTER_DEFAULTS["bgg_rating"],
        None,
        [year_min, CURRENT_YEAR],
        [],
    )


# ---------------------------------------------------------------------------
# Helpers — used by collection.py update_grid
# ---------------------------------------------------------------------------


def apply_filters_and_sort(
    games: list[dict[str, Any]],
    *,
    name: str = "",
    players: list[int] | None = None,
    play_time: list[int] | None = None,
    complexity: list[float] | None = None,
    bgg_rating: list[float] | None = None,
    bgg_rank_max: int | None = None,
    year: list[int] | None = None,
    categories: list[str] | None = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    """Filter and sort a list of serialized game dicts."""
    result = games

    if name:
        q = name.lower()
        result = [g for g in result if q in (g.get("name") or "").lower()]

    if players:
        lo, hi = players
        result = [
            g
            for g in result
            if (g.get("min_players") or 0) <= hi
            and (g.get("max_players") or 0) >= lo
        ]

    if play_time:
        lo, hi = play_time
        result = [
            g
            for g in result
            if (g.get("min_play_time") or 0) <= hi
            and (g.get("max_play_time") or 0) >= lo
        ]

    if complexity and complexity != [1.0, 5.0]:
        flo, fhi = complexity
        result = [
            g
            for g in result
            if g.get("complexity") is not None
            and flo <= g["complexity"] <= fhi
        ]

    if bgg_rating and bgg_rating != [1.0, 10.0]:
        flo, fhi = bgg_rating
        result = [
            g
            for g in result
            if g.get("bgg_rating") is not None
            and flo <= g["bgg_rating"] <= fhi
        ]

    if bgg_rank_max is not None:
        result = [
            g
            for g in result
            if g.get("bgg_rank") is not None and g["bgg_rank"] <= bgg_rank_max
        ]

    if year:
        lo, hi = year
        result = [
            g for g in result if lo <= (g.get("release_year") or 0) <= hi
        ]

    if categories:
        cat_set = set(categories)
        result = [
            g for g in result if cat_set & set(g.get("categories") or [])
        ]

    reverse = sort_dir == "desc"

    def sort_key(g: dict[str, Any]) -> tuple[bool, Any]:
        val = g.get(sort_by)
        return (val is None, val if val is not None else "")

    return sorted(result, key=sort_key, reverse=reverse)


def game_to_dict(game: Any, ownership_status: Any | None) -> dict[str, Any]:
    """Serialize a Game SQLModel instance to a plain dict for dcc.Store."""
    return {
        "bgg_id": game.bgg_id,
        "name": game.name,
        "image_path": game.image_path,
        "bgg_rating": game.bgg_rating,
        "bgg_rank": game.bgg_rank,
        "min_players": game.min_players,
        "max_players": game.max_players,
        "min_play_time": game.min_play_time,
        "max_play_time": game.max_play_time,
        "complexity": game.complexity,
        "release_year": game.release_year,
        "min_age": game.min_age,
        "categories": [c.name for c in (game.categories or [])],
        "ownership_status": ownership_status.name
        if ownership_status
        else None,
    }
