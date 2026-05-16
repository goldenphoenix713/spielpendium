from unittest.mock import MagicMock

import dash
import dash_mantine_components as dmc

# Mock dash.register_page before importing the module to prevent side-effects
dash.register_page = MagicMock()  # type: ignore[assignment, unused-ignore]  # ty: ignore[invalid-assignment]

from dash import html  # noqa: E402

from pages.collection import create_game_card  # noqa: E402
from tests.test_models import create_mock_game  # noqa: E402
from util.models import OwnershipStatus  # noqa: E402


def test_create_game_card_basic() -> None:
    # Set up mock game
    game = create_mock_game(1, "Settlers of Catan")
    game.bgg_rating = 8.5
    game.min_players = 3
    game.max_players = 4
    game.min_play_time = 60
    game.max_play_time = 120

    status = OwnershipStatus(name="owned")

    # Generate component
    card_div = create_game_card(game, status)

    # Verify it is a Div component wrapping a Card
    assert isinstance(card_div, html.Div)
    assert card_div.id == {"type": "game-card", "index": 1}  # ty: ignore[unresolved-attribute]
    # Use to_plotly_json() to verify props in tests
    assert card_div.to_plotly_json()["props"]["n_clicks"] == 0

    card = card_div.children
    assert isinstance(card, dmc.Card)
    assert isinstance(card.children, list)

    box_component = card.children[1]
    name_text = box_component.children
    group_component = card.children[2]
    assert isinstance(group_component.children, list)
    rating_badge = group_component.children[1]

    assert name_text.children == "Settlers of Catan"
    assert rating_badge.children == "8.5"

    stats_text = card.children[3]
    assert "3-4 Players" in stats_text.children
    assert "60-120 Min" in stats_text.children

    button = card.children[4]
    assert isinstance(button, dmc.Button)


def test_create_game_card_no_rating_or_image() -> None:
    game = create_mock_game(99, "Mystery Game")
    game.bgg_rating = None
    game.image_path = None

    card_div = create_game_card(game, None)
    card = card_div.children
    assert isinstance(card.children, list)  # ty: ignore[unresolved-attribute]

    # Check rating fallback
    group_component = card.children[2]  # ty: ignore[unresolved-attribute]
    assert isinstance(group_component.children, list)
    rating_badge = group_component.children[1]
    assert rating_badge.children == "N/A"

    # Check image fallback
    image_section = card.children[0]  # ty: ignore[unresolved-attribute]
    image = image_section.children
    assert "placehold.co" in image.src
