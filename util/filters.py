from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, ctx, dcc, no_update
from dash_iconify import DashIconify

from util.settings import get_active_username

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CURRENT_YEAR = datetime.now().year
YEAR_MIN = (
    1970  # Slider floor — games older than this fall into the 1970 bucket
)
PLAY_TIME_MAX = 240  # Slider cap — "240+" label; games longer than this are included at max
PLAYERS_MAX = 10  # Slider cap — "10+" label

OWNERSHIP_LABELS: dict[str, str] = {
    "owned": "Owned",
    "prevowned": "Prev. Owned",
    "want": "Want to Buy",
}

FILTER_DEFAULTS: dict[str, Any] = {
    "sort_by": "name",
    "sort_dir": "asc",
    "name": "",
    "players": [1, PLAYERS_MAX],
    "play_time": [0, PLAY_TIME_MAX],
    "complexity": [1.0, 5.0],
    "bgg_rating": [1.0, 10.0],
    "bgg_rank_max": None,
    "year": [YEAR_MIN, CURRENT_YEAR],
    "age": [1, 18],
    "categories": [],
    "authors": [],
    "publishers": [],
    "ownership": ["owned"],
}


# ---------------------------------------------------------------------------
# Shared component builder
# ---------------------------------------------------------------------------


def _build_filter_components(location: str) -> list[Any]:
    def cid(control: str) -> dict[str, str]:
        return {"location": location, "control": control}

    sort_by_ctrl = dmc.Select(
        id=cid("sort_by"),
        label="Sort by",
        value=FILTER_DEFAULTS["sort_by"],
        data=[
            {"label": "Name", "value": "name"},
            {"label": "BGG Rating", "value": "bgg_rating"},
            {"label": "BGG Rank", "value": "bgg_rank"},
            {"label": "Year Released", "value": "release_year"},
            {"label": "Complexity", "value": "complexity"},
            {"label": "Play Time", "value": "min_play_time"},
            {"label": "Minimum Age", "value": "min_age"},
        ],
        allowDeselect=False,
    )

    sort_dir_ctrl = dmc.SegmentedControl(
        id=cid("sort_dir"),
        value=FILTER_DEFAULTS["sort_dir"],
        data=[
            {"label": "↑ Asc", "value": "asc"},
            {"label": "↓ Desc", "value": "desc"},
        ],
        fullWidth=True,
    )

    name_search = dmc.TextInput(
        id=cid("name"),
        label="Name",
        placeholder="Search…",
        value=FILTER_DEFAULTS["name"],
        debounce=True,
        leftSection=DashIconify(icon="tabler:search", width=16),
    )

    ownership = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Ownership", size="sm", fw=500),
            dmc.ChipGroup(
                id=cid("ownership"),
                value=FILTER_DEFAULTS["ownership"],
                multiple=True,
                children=[
                    dmc.Chip(label, value=val, size="xs")
                    for val, label in OWNERSHIP_LABELS.items()
                ],
            ),
            dmc.Alert(
                "Showing non-owned games may return many results. "
                "Consider adding other filters.",
                id={"location": location, "control": "ownership_warning"},
                color="yellow",
                variant="light",
                p="xs",
                style={"display": "none"},
            ),
        ],
    )

    players = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Players", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("players"),
                min=1,
                max=PLAYERS_MAX,
                step=1,
                minRange=1,
                value=FILTER_DEFAULTS["players"],
                label={"function": "playersFormatter"},  # ty: ignore[invalid-argument-type]
                marks=[
                    {
                        "value": i,
                        "label": ("10+" if i == PLAYERS_MAX else str(i))
                        if i % 2 == 0
                        else "",
                    }
                    for i in range(1, PLAYERS_MAX + 1)
                ],
                mb="xs",
            ),
        ],
    )

    play_time = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Play Time (min)", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("play_time"),
                min=0,
                max=PLAY_TIME_MAX,
                step=15,
                minRange=1,
                value=FILTER_DEFAULTS["play_time"],
                label={"function": "playTimeFormatter"},  # ty: ignore[invalid-argument-type]
                marks=[
                    {
                        "value": v,
                        "label": ("240+" if v == PLAY_TIME_MAX else str(v))
                        if v % 60 == 0
                        else "",
                    }
                    for v in range(0, PLAY_TIME_MAX + 1, 15)
                ],
                mb="xs",
            ),
        ],
    )

    complexity = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Complexity (Weight)", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("complexity"),
                min=1.0,
                max=5.0,
                step=0.25,
                minRange=0.1,
                value=FILTER_DEFAULTS["complexity"],
                marks=[{"value": v, "label": str(v)} for v in [1, 2, 3, 4, 5]],
                mb="xs",
            ),
        ],
    )

    bgg_rating = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("BGG Rating", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("bgg_rating"),
                min=1.0,
                max=10.0,
                step=0.1,
                minRange=0.1,
                value=FILTER_DEFAULTS["bgg_rating"],
                marks=[{"value": v, "label": str(v)} for v in range(1, 11)],
                mb="xs",
            ),
        ],
    )

    bgg_rank = dmc.NumberInput(
        id=cid("bgg_rank_max"),
        label="BGG Rank — better than",
        placeholder="Any rank",
        value=FILTER_DEFAULTS["bgg_rank_max"],
        min=1,
    )

    year = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Year Released", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("year"),
                min=YEAR_MIN,
                max=CURRENT_YEAR,
                step=1,
                minRange=1,
                value=FILTER_DEFAULTS["year"],
                label={"function": "yearFormatter"},  # ty: ignore[invalid-argument-type]
                marks=[
                    {
                        "value": v,
                        "label": ("≤1970" if v == YEAR_MIN else str(v)),
                    }
                    for v in range(YEAR_MIN, CURRENT_YEAR + 1, 10)
                ],
                mb="xs",
            ),
        ],
    )

    age = dmc.Stack(
        gap=4,
        children=[
            dmc.Text("Minimum Age", size="sm", fw=500),
            dmc.RangeSlider(
                id=cid("age"),
                min=1,
                max=18,
                step=1,
                minRange=1,
                value=FILTER_DEFAULTS["age"],
                label={"function": "ageFormatter"},  # ty: ignore[invalid-argument-type]
                marks=[
                    {"value": v, "label": ("18+" if v == 18 else str(v))}
                    for v in [1, 5, 10, 14, 18]
                ],
                mb="xs",
            ),
        ],
    )

    categories = dmc.MultiSelect(
        id=cid("categories"),
        label="Categories",
        placeholder="All categories",
        value=FILTER_DEFAULTS["categories"],
        searchable=True,
        clearable=True,
        data=[],
    )

    authors = dmc.MultiSelect(
        id=cid("authors"),
        label="Designers",
        placeholder="All designers",
        value=FILTER_DEFAULTS["authors"],
        searchable=True,
        clearable=True,
        data=[],
    )

    publishers = dmc.MultiSelect(
        id=cid("publishers"),
        label="Publishers",
        placeholder="All publishers",
        value=FILTER_DEFAULTS["publishers"],
        searchable=True,
        clearable=True,
        data=[],
    )

    return [
        dmc.Divider(label="Sort", labelPosition="left"),
        sort_by_ctrl,
        sort_dir_ctrl,
        dmc.Group(
            [
                dmc.Text("Filters", size="sm", fw=700),
                dmc.Button(
                    "Clear All",
                    id={"location": location, "control": "clear_btn"},
                    size="compact-xs",
                    variant="subtle",
                    color="gray",
                    rightSection=DashIconify(icon="tabler:x", width=12),
                ),
            ],
            justify="space-between",
            mt="md",
            mb="xs",
            style={
                "position": "sticky",
                "top": 0,
                "zIndex": 10,
                "backgroundColor": "var(--mantine-color-body)",
                "paddingTop": "4px",
                "paddingBottom": "4px",
                "borderBottom": "1px solid var(--mantine-color-default-border)",
            },
        ),
        name_search,
        dmc.Space(h="md"),
        dmc.Accordion(
            multiple=True,
            value=["core"],
            children=[
                dmc.AccordionItem(
                    value="core",
                    children=[
                        dmc.AccordionControl("Core Info", fw=500),
                        dmc.AccordionPanel(
                            dmc.Stack([ownership, year, age], gap="md")
                        ),
                    ],
                ),
                dmc.AccordionItem(
                    value="gameplay",
                    children=[
                        dmc.AccordionControl("Gameplay", fw=500),
                        dmc.AccordionPanel(
                            dmc.Stack(
                                [players, play_time, complexity],
                                gap="md",
                            )
                        ),
                    ],
                ),
                dmc.AccordionItem(
                    value="credits",
                    children=[
                        dmc.AccordionControl("Credits & More", fw=500),
                        dmc.AccordionPanel(
                            dmc.Stack(
                                [
                                    bgg_rating,
                                    bgg_rank,
                                    categories,
                                    authors,
                                    publishers,
                                ],
                                gap="md",
                            )
                        ),
                    ],
                ),
            ],
        ),
        dmc.Space(h="xl"),
        dmc.Anchor(
            dmc.Button(
                "View on BoardGameGeek",
                variant="light",
                color="orange",
                fullWidth=True,
                leftSection=DashIconify(
                    icon="simple-icons:boardgamegeek", width=16
                ),
            ),
            href=f"https://boardgamegeek.com/collection/user/{get_active_username()}",
            target="_blank",
            underline="never",
            mb="md",
        ),
        dmc.Group(
            dmc.Image(
                id={"location": location, "control": "bgg_logo"},
                src="/assets/powered-by-bgg-reversed-rgb.svg",
                h=40,
                fit="contain",
                style={"opacity": 0.8},
            ),
            justify="center",
            mt="xl",
            mb="md",
        ),
    ]


# ---------------------------------------------------------------------------
# Public layout builders
# ---------------------------------------------------------------------------


def generate_sidebar() -> dmc.Stack:
    """Sidebar for desktop — contains the filters-store and all controls."""
    return dmc.Stack(
        gap="lg",
        p="md",
        children=[
            dcc.Store(id="filters-store", storage_type="local"),
            *_build_filter_components("sidebar"),
        ],
    )


def generate_drawer_content() -> list[Any]:
    """Content for the mobile drawer — same controls with location='drawer'."""
    return _build_filter_components("drawer")


# ---------------------------------------------------------------------------
# Callback 1: populate filter bounds + restore saved state on collection load
# ---------------------------------------------------------------------------
@callback(
    # category options
    Output({"location": ALL, "control": "categories"}, "data"),
    # sort / search
    Output({"location": ALL, "control": "sort_by"}, "value"),
    Output({"location": ALL, "control": "sort_dir"}, "value"),
    Output({"location": ALL, "control": "name"}, "value"),
    # players
    Output({"location": ALL, "control": "players"}, "max"),
    Output({"location": ALL, "control": "players"}, "value"),
    # play time
    Output({"location": ALL, "control": "play_time"}, "max"),
    Output({"location": ALL, "control": "play_time"}, "value"),
    # complexity / rating / rank / ownership (value-only)
    Output({"location": ALL, "control": "complexity"}, "value"),
    Output({"location": ALL, "control": "bgg_rating"}, "value"),
    Output({"location": ALL, "control": "bgg_rank_max"}, "value"),
    Output({"location": ALL, "control": "ownership"}, "value"),
    # year
    Output({"location": ALL, "control": "year"}, "min"),
    Output({"location": ALL, "control": "year"}, "value"),
    # category value
    Output({"location": ALL, "control": "categories"}, "value"),
    # age value
    Output({"location": ALL, "control": "age"}, "value"),
    # authors / publishers data and value
    Output({"location": ALL, "control": "authors"}, "data"),
    Output({"location": ALL, "control": "authors"}, "value"),
    Output({"location": ALL, "control": "publishers"}, "data"),
    Output({"location": ALL, "control": "publishers"}, "value"),
    Input("collection-store", "data"),
    State("filters-store", "data"),
    prevent_initial_call=True,
)
def populate_filter_bounds(
    games: list[dict[str, Any]],
    saved: dict[str, Any] | None,
) -> tuple[Any, ...]:
    """Set filter bounds from the collection and restore any saved state."""
    sf = saved or {}

    def both(val: Any) -> list[Any]:
        return [val, val]

    if not games:
        return (
            both([]),  # categories data
            both(FILTER_DEFAULTS["sort_by"]),
            both(FILTER_DEFAULTS["sort_dir"]),
            both(FILTER_DEFAULTS["name"]),
            both(PLAYERS_MAX),  # players max
            both(FILTER_DEFAULTS["players"]),  # players value
            both(PLAY_TIME_MAX),  # play_time max
            both(FILTER_DEFAULTS["play_time"]),  # play_time value
            both(FILTER_DEFAULTS["complexity"]),
            both(FILTER_DEFAULTS["bgg_rating"]),
            both(FILTER_DEFAULTS["bgg_rank_max"]),
            both(FILTER_DEFAULTS["ownership"]),
            both(YEAR_MIN),  # year min
            both(FILTER_DEFAULTS["year"]),  # year value
            both(FILTER_DEFAULTS["categories"]),
            both(FILTER_DEFAULTS["age"]),
            both([]),  # authors data
            both(FILTER_DEFAULTS["authors"]),
            both([]),  # publishers data
            both(FILTER_DEFAULTS["publishers"]),
        )

    all_cats = sorted({
        cat for g in games for cat in (g.get("categories") or [])
    })
    cat_data = [{"label": c, "value": c} for c in all_cats]

    all_authors = sorted({
        author for g in games for author in (g.get("authors") or [])
    })
    author_data = [{"label": a, "value": a} for a in all_authors]

    all_publishers = sorted({
        publisher for g in games for publisher in (g.get("publishers") or [])
    })
    publisher_data = [{"label": p, "value": p} for p in all_publishers]

    max_players = min(
        max(
            (g.get("max_players") or PLAYERS_MAX for g in games),
            default=PLAYERS_MAX,
        ),
        PLAYERS_MAX,
    )
    max_time = min(
        max(
            (g.get("max_play_time") or PLAY_TIME_MAX for g in games),
            default=PLAY_TIME_MAX,
        ),
        PLAY_TIME_MAX,
    )
    # Cap min_year at YEAR_MIN so pre-1970 games don't stretch the slider
    min_year = max(
        min(
            (g.get("release_year") or CURRENT_YEAR for g in games),
            default=YEAR_MIN,
        ),
        YEAR_MIN,
    )

    return (
        both(cat_data),
        both(sf.get("sort_by", FILTER_DEFAULTS["sort_by"])),
        both(sf.get("sort_dir", FILTER_DEFAULTS["sort_dir"])),
        both(sf.get("name", FILTER_DEFAULTS["name"])),
        both(max_players),
        both(sf.get("players", [1, max_players])),
        both(max_time),
        both(sf.get("play_time", [0, max_time])),
        both(sf.get("complexity", FILTER_DEFAULTS["complexity"])),
        both(sf.get("bgg_rating", FILTER_DEFAULTS["bgg_rating"])),
        both(sf.get("bgg_rank_max", FILTER_DEFAULTS["bgg_rank_max"])),
        both(sf.get("ownership", FILTER_DEFAULTS["ownership"])),
        both(min_year),
        both(sf.get("year", [min_year, CURRENT_YEAR])),
        both(sf.get("categories", FILTER_DEFAULTS["categories"])),
        both(sf.get("age", FILTER_DEFAULTS["age"])),
        both(author_data),
        both(sf.get("authors", FILTER_DEFAULTS["authors"])),
        both(publisher_data),
        both(sf.get("publishers", FILTER_DEFAULTS["publishers"])),
    )


# ---------------------------------------------------------------------------
# Callback 2: save any filter change to filters-store
# ---------------------------------------------------------------------------
@callback(
    Output("filters-store", "data"),
    Input({"location": ALL, "control": ALL}, "value"),
    State("filters-store", "data"),
)
def save_filter_state(
    _values: list[Any],
    current_store: dict[str, Any] | None,
) -> dict[str, Any]:
    """Generic saver: when any filter component changes, update filters-store."""
    triggered = ctx.triggered_id

    if not triggered:
        return current_store or dict(FILTER_DEFAULTS)

    store = dict(current_store or FILTER_DEFAULTS)

    if not ctx.triggered:
        return store

    new_val = ctx.triggered[0]["value"]

    if isinstance(triggered, dict):
        control = triggered.get("control", "")
        # Skip clear_btn
        if control in ("clear_btn", "ownership_warning"):
            return cast("dict[str, Any]", no_update)
        store[control] = new_val

    return store


# ---------------------------------------------------------------------------
# Callback 3: show/hide ownership warning
# ---------------------------------------------------------------------------
@callback(
    Output({"location": ALL, "control": "ownership_warning"}, "style"),
    Input({"location": ALL, "control": "ownership"}, "value"),
)
def toggle_ownership_warning(
    ownership_values: list[list[str]],
) -> list[dict[str, str]]:
    """Show a warning when non-owned games are included."""
    # Use first non-None value as the canonical ownership
    ownership = next((v for v in ownership_values if v is not None), ["owned"])
    if not ownership or set(ownership) == {"owned"}:
        hidden = {"display": "none"}
        return [hidden, hidden]
    visible: dict[str, str] = {}
    return [visible, visible]


# ---------------------------------------------------------------------------
# Callback 4: clear all filters
# ---------------------------------------------------------------------------
@callback(
    Output(
        {"location": ALL, "control": "sort_by"}, "value", allow_duplicate=True
    ),
    Output(
        {"location": ALL, "control": "sort_dir"}, "value", allow_duplicate=True
    ),
    Output(
        {"location": ALL, "control": "name"}, "value", allow_duplicate=True
    ),
    Output(
        {"location": ALL, "control": "players"}, "value", allow_duplicate=True
    ),
    Output(
        {"location": ALL, "control": "play_time"},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"location": ALL, "control": "complexity"},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"location": ALL, "control": "bgg_rating"},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"location": ALL, "control": "bgg_rank_max"},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"location": ALL, "control": "year"}, "value", allow_duplicate=True
    ),
    Output(
        {"location": ALL, "control": "categories"},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"location": ALL, "control": "ownership"},
        "value",
        allow_duplicate=True,
    ),
    Input({"location": ALL, "control": "clear_btn"}, "n_clicks"),
    State({"location": ALL, "control": "players"}, "max"),
    State({"location": ALL, "control": "play_time"}, "max"),
    State({"location": ALL, "control": "year"}, "min"),
    prevent_initial_call=True,
)
def clear_filters(
    _n_clicks: list[int | None],
    players_max: list[int],
    time_max: list[int],
    year_min: list[int],
) -> tuple[Any, ...]:
    """Reset all filters to defaults."""
    if not any(_n_clicks):
        return cast("tuple[Any, ...]", no_update)

    pm = players_max[0] if players_max else 10
    tm = time_max[0] if time_max else 300
    ym = year_min[0] if year_min else 1970

    def both(val: Any) -> list[Any]:
        return [val, val]

    return (
        both(FILTER_DEFAULTS["sort_by"]),
        both(FILTER_DEFAULTS["sort_dir"]),
        both(FILTER_DEFAULTS["name"]),
        both([1, pm]),
        both([0, tm]),
        both(FILTER_DEFAULTS["complexity"]),
        both(FILTER_DEFAULTS["bgg_rating"]),
        both(None),
        both([ym, CURRENT_YEAR]),
        both([]),
        both(FILTER_DEFAULTS["ownership"]),
    )


# ---------------------------------------------------------------------------
# Callback 5: toggle mobile drawer
# ---------------------------------------------------------------------------
@callback(
    Output("mobile-filter-drawer", "opened"),
    Input("burger-button", "n_clicks"),
    State("mobile-filter-drawer", "opened"),
    prevent_initial_call=True,
)
def toggle_mobile_drawer(_: int | None, is_open: bool) -> bool:
    """Toggle the mobile filter drawer open/closed."""
    return not is_open


# ---------------------------------------------------------------------------
# Helpers — used by collection.py
# ---------------------------------------------------------------------------


def apply_filters_and_sort(
    games: list[dict[str, Any]],
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Filter and sort games using the filters-store dict."""
    result = games

    name = filters.get("name") or ""
    if name:
        q = name.lower()
        result = [g for g in result if q in (g.get("name") or "").lower()]

    ownership: list[str] = filters.get("ownership") or []
    if ownership:
        mapped_ownership = {"own" if o == "owned" else o for o in ownership}
        result = [
            g for g in result if mapped_ownership & set(g.get("statuses", []))
        ]

    players: list[int] | None = filters.get("players")
    if players:
        lo, hi = players
        if hi >= PLAYERS_MAX:
            # Right handle at cap — include games with more players too
            result = [g for g in result if (g.get("max_players") or 0) >= lo]
        else:
            result = [
                g
                for g in result
                if (g.get("min_players") or 0) <= hi
                and (g.get("max_players") or 0) >= lo
            ]

    play_time: list[int] | None = filters.get("play_time")
    if play_time:
        lo, hi = play_time
        if hi >= PLAY_TIME_MAX:
            # Right handle at cap — include games longer than 240 min too
            result = [
                g
                for g in result
                if (g.get("min_play_time") or 0) <= PLAY_TIME_MAX
                and (g.get("max_play_time") or 0) >= lo
            ]
        else:
            result = [
                g
                for g in result
                if (g.get("min_play_time") or 0) <= hi
                and (g.get("max_play_time") or 0) >= lo
            ]

    complexity: list[float] | None = filters.get("complexity")
    if complexity and complexity != [1.0, 5.0]:
        flo, fhi = complexity
        result = [
            g
            for g in result
            if g.get("complexity") is not None
            and flo <= g["complexity"] <= fhi
        ]

    bgg_rating: list[float] | None = filters.get("bgg_rating")
    if bgg_rating and bgg_rating != [1.0, 10.0]:
        flo, fhi = bgg_rating
        result = [
            g
            for g in result
            if g.get("bgg_rating") is not None
            and flo <= g["bgg_rating"] <= fhi
        ]

    bgg_rank_max_val: int | str | None = filters.get("bgg_rank_max")
    if bgg_rank_max_val is not None and bgg_rank_max_val != "":
        bgg_rank_max = int(bgg_rank_max_val)
        result = [
            g
            for g in result
            if g.get("bgg_rank") is not None and g["bgg_rank"] <= bgg_rank_max
        ]

    year: list[int] | None = filters.get("year")
    if year:
        lo, hi = year
        if lo <= YEAR_MIN:
            # Left handle is at the floor — include all games older than YEAR_MIN too
            result = [
                g
                for g in result
                if (g.get("release_year") is None or g["release_year"] <= hi)
            ]
        else:
            result = [
                g for g in result if lo <= (g.get("release_year") or 0) <= hi
            ]

    categories: list[str] | None = filters.get("categories")
    if categories:
        cat_set = set(categories)
        result = [
            g for g in result if cat_set & set(g.get("categories") or [])
        ]

    authors: list[str] | None = filters.get("authors")
    if authors:
        auth_set = set(authors)
        result = [g for g in result if auth_set & set(g.get("authors") or [])]

    publishers: list[str] | None = filters.get("publishers")
    if publishers:
        pub_set = set(publishers)
        result = [
            g for g in result if pub_set & set(g.get("publishers") or [])
        ]

    age: list[int] | None = filters.get("age")
    if age:
        lo, hi = age
        if hi >= 18:
            # Right handle at max — include games for 18+ too
            result = [g for g in result if (g.get("min_age") or 0) >= lo]
        else:
            result = [g for g in result if lo <= (g.get("min_age") or 0) <= hi]

    sort_by: str = filters.get("sort_by") or "name"
    sort_dir: str = filters.get("sort_dir") or "asc"
    reverse = sort_dir == "desc"

    def sort_key(g: dict[str, Any]) -> tuple[bool, Any]:
        val = g.get(sort_by)
        return (val is None, val if val is not None else "")

    return sorted(result, key=sort_key, reverse=reverse)


def game_to_dict(game: Any, collection_item: Any | None) -> dict[str, Any]:
    """Serialize a Game SQLModel instance to a plain dict for dcc.Store."""
    status_name = (
        collection_item.ownership_status.name
        if collection_item and hasattr(collection_item, "ownership_status")
        else None
    )

    # Extract status list
    statuses = (
        getattr(collection_item, "statuses", []) if collection_item else []
    )

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
        "authors": [a.name for a in (game.authors or [])],
        "publishers": [p.name for p in (game.publishers or [])],
        "ownership_status": status_name,
        "statuses": statuses,
    }


@callback(
    Output({"location": ALL, "control": "bgg_logo"}, "src"),
    Input("theme-store", "data"),
)
def update_bgg_logo_theme(theme: str | None) -> list[str]:
    """Switch the BGG logo asset based on the current theme."""
    asset = (
        "/assets/powered-by-bgg-rgb.svg"
        if theme == "light"
        else "/assets/powered-by-bgg-reversed-rgb.svg"
    )
    # Return same asset for both sidebar and drawer logos
    return [asset] * len(ctx.outputs_list)
