from __future__ import annotations

from typing import Any
from unittest.mock import patch

from util.filters import (
    FILTER_DEFAULTS,
    PLAY_TIME_MAX,
    PLAYERS_MAX,
    YEAR_MIN,
    apply_filters_and_sort,
    clear_filters,
    game_to_dict,
    generate_drawer_content,
    generate_sidebar,
    populate_filter_bounds,
    save_filter_state,
    toggle_mobile_drawer,
    toggle_ownership_warning,
)
from util.models import (
    Category,
    CollectionItem,
    Game,
    OwnershipStatus,
    Person,
    Publisher,
)


def get_mock_game(name: str, **kwargs: Any) -> dict[str, Any]:
    base = {
        "name": name,
        "bgg_id": 1,
        "ownership_status": "owned",
        "min_players": 1,
        "max_players": 4,
        "min_play_time": 30,
        "max_play_time": 60,
        "complexity": 2.5,
        "bgg_rating": 7.5,
        "bgg_rank": 100,
        "release_year": 2020,
        "min_age": 10,
        "categories": [],
        "authors": [],
        "publishers": [],
    }
    base.update(kwargs)
    return base


@patch("util.filters.get_active_username")
def test_component_builders(mock_get_username: Any):
    mock_get_username.return_value = "testuser"
    sidebar = generate_sidebar()
    assert sidebar is not None

    drawer = generate_drawer_content()
    assert isinstance(drawer, list)
    assert len(drawer) > 0


def test_populate_filter_bounds():
    games = [
        get_mock_game(
            "G1", categories=["Cat1"], authors=["Auth1"], publishers=["Pub1"]
        )
    ]
    saved = {"sort_by": "bgg_rating"}

    result = populate_filter_bounds(games, saved)
    # result is a tuple of 21 elements (based on current unified implementation)
    assert len(result) == 21

    # Check if sort_by is restored
    assert result[1] == ["bgg_rating", "bgg_rating"]
    # Check if categories data is populated (still using both() helper)
    assert result[0] == [
        [{"label": "Cat1", "value": "Cat1"}],
        [{"label": "Cat1", "value": "Cat1"}],
    ]


def test_save_filter_state():
    # Mock dash context
    with patch("util.filters.ctx") as mock_ctx:
        mock_ctx.triggered_id = {"location": "sidebar", "control": "name"}
        mock_ctx.triggered = [
            {
                "prop_id": '{"location": "sidebar", "control": "name"}.value',
                "value": "new_name",
            }
        ]
        mock_ctx.inputs_list = [
            [{"id": {"location": "sidebar", "control": "name"}}]
        ]

        all_values = ["new_name"]
        current_store = {"name": "old_name"}

        result = save_filter_state(all_values, current_store)
        assert result["name"] == "new_name"


def test_toggle_ownership_warning():
    # Only owned
    assert toggle_ownership_warning([["owned"]]) == [
        {"display": "none"},
        {"display": "none"},
    ]
    # Includes want
    assert toggle_ownership_warning([["owned", "want"]]) == [{}, {}]


def test_clear_filters():
    # Mock dash context
    with patch("util.filters.ctx"):
        result = clear_filters([1], [10], [300], [1970])
        assert result[0] == ["name", "name"]  # sort_by
        assert result[2] == ["", ""]  # name


def test_toggle_mobile_drawer():
    assert toggle_mobile_drawer(1, False) is True
    assert toggle_mobile_drawer(1, True) is False


def test_apply_filters_name():
    games = [
        get_mock_game("Catan"),
        get_mock_game("Pandemic"),
    ]
    filters = {**FILTER_DEFAULTS, "name": "pan", "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Pandemic"


def test_apply_filters_ownership():
    games = [
        get_mock_game("G1", statuses=["own"]),
        get_mock_game("G2", statuses=["want"]),
    ]
    filters = {**FILTER_DEFAULTS, "ownership": ["want"]}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "G2"


def test_apply_filters_players_at_cap():
    games = [
        get_mock_game("Small", min_players=1, max_players=2),
        get_mock_game("Big", min_players=2, max_players=12),
    ]
    # Filter for 5+ players (cap is 10)
    filters = {**FILTER_DEFAULTS, "players": [5, PLAYERS_MAX], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Big"


def test_apply_filters_players_range():
    games = [
        get_mock_game("P2", min_players=2, max_players=2),
        get_mock_game("P4", min_players=4, max_players=4),
    ]
    filters = {**FILTER_DEFAULTS, "players": [3, 4], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "P4"


def test_apply_filters_play_time_at_cap():
    games = [
        get_mock_game("Short", min_play_time=30, max_play_time=60),
        get_mock_game("Long", min_play_time=120, max_play_time=300),
    ]
    # Filter for 240+ min (cap is 240)
    filters = {
        **FILTER_DEFAULTS,
        "play_time": [200, PLAY_TIME_MAX],
        "ownership": [],
    }
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Long"


def test_apply_filters_complexity():
    games = [
        get_mock_game("Easy", complexity=1.5),
        get_mock_game("Hard", complexity=4.5),
    ]
    filters = {**FILTER_DEFAULTS, "complexity": [4.0, 5.0], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Hard"


def test_apply_filters_rating():
    games = [
        get_mock_game("Good", bgg_rating=8.5),
        get_mock_game("Bad", bgg_rating=4.5),
    ]
    filters = {**FILTER_DEFAULTS, "bgg_rating": [8.0, 10.0], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Good"


def test_apply_filters_rank():
    games = [
        get_mock_game("Top", bgg_rank=10),
        get_mock_game("Bottom", bgg_rank=1000),
    ]
    filters = {**FILTER_DEFAULTS, "bgg_rank_max": 50, "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Top"


def test_apply_filters_year():
    games = [
        get_mock_game("Old", release_year=1950),
        get_mock_game("New", release_year=2020),
    ]
    # Filter for <= 1980
    filters = {**FILTER_DEFAULTS, "year": [YEAR_MIN, 1980], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Old"


def test_apply_filters_categories():
    games = [
        get_mock_game("War", categories=["Wargame", "Strategy"]),
        get_mock_game("Party", categories=["Party Game"]),
    ]
    filters = {**FILTER_DEFAULTS, "categories": ["Wargame"], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "War"


def test_apply_filters_authors():
    games = [
        get_mock_game("Knia", authors=["Reiner Knizia"]),
        get_mock_game("Rose", authors=["Uwe Rosenberg"]),
    ]
    filters = {
        **FILTER_DEFAULTS,
        "authors": ["Uwe Rosenberg"],
        "ownership": [],
    }
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Rose"


def test_apply_filters_age_at_cap():
    games = [
        get_mock_game("Kids", min_age=5),
        get_mock_game("Adults", min_age=18),
    ]
    filters = {**FILTER_DEFAULTS, "age": [14, 18], "ownership": []}
    result = apply_filters_and_sort(games, filters)
    assert len(result) == 1
    assert result[0]["name"] == "Adults"


def test_sorting():
    games = [
        get_mock_game("B", bgg_rating=7.0),
        get_mock_game("A", bgg_rating=8.0),
    ]
    # Sort by name asc
    filters = {
        **FILTER_DEFAULTS,
        "sort_by": "name",
        "sort_dir": "asc",
        "ownership": [],
    }
    result = apply_filters_and_sort(games, filters)
    assert result[0]["name"] == "A"

    # Sort by rating desc
    filters = {
        **FILTER_DEFAULTS,
        "sort_by": "bgg_rating",
        "sort_dir": "desc",
        "ownership": [],
    }
    result = apply_filters_and_sort(games, filters)
    assert result[0]["name"] == "A"


def test_game_to_dict():
    game = Game(
        bgg_id=1,
        name="Test",
        version=1.0,
        description="Desc",
        min_players=1,
        max_players=4,
        min_play_time=30,
        max_play_time=60,
        complexity=2.5,
        bgg_rating=7.5,
        release_year=2021,
        min_age=10,
    )  # ty:ignore[missing-argument]
    # Use real SQLModel instances
    game.categories = [Category(id=b"1", name="Cat1")]
    game.authors = [Person(id=b"2", name="Auth1")]
    game.publishers = [Publisher(id=b"3", name="Pub1")]

    status = OwnershipStatus(id=b"4", name="owned")
    item = CollectionItem(
        collection_id=b"1",
        game_id=b"1",
        ownership_status_id=b"4",
        ownership_status=status,
        statuses=["own", "wanttoplay"],
    )

    d = game_to_dict(game, item)
    assert d["name"] == "Test"
    assert d["categories"] == ["Cat1"]
    assert d["authors"] == ["Auth1"]
    assert d["publishers"] == ["Pub1"]
    assert d["ownership_status"] == "owned"
    assert d["statuses"] == ["own", "wanttoplay"]


def test_apply_filters_expansions():
    games = [
        get_mock_game("Base Game", categories=["Adventure"]),
        get_mock_game(
            "Expansion DLC",
            categories=["Adventure", "Expansion for Base-game"],
        ),
    ]

    # Show all
    filters_all = {**FILTER_DEFAULTS, "expansions": "all", "ownership": []}
    result_all = apply_filters_and_sort(games, filters_all)
    assert len(result_all) == 2

    # Hide expansions
    filters_hide = {**FILTER_DEFAULTS, "expansions": "hide", "ownership": []}
    result_hide = apply_filters_and_sort(games, filters_hide)
    assert len(result_hide) == 1
    assert result_hide[0]["name"] == "Base Game"

    # Only expansions
    filters_only = {**FILTER_DEFAULTS, "expansions": "only", "ownership": []}
    result_only = apply_filters_and_sort(games, filters_only)
    assert len(result_only) == 1
    assert result_only[0]["name"] == "Expansion DLC"
