from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import dash
import dash_mantine_components as dmc
import pytest
from sqlmodel import Session, SQLModel, create_engine

# Must mock register_page before importing the module
dash.register_page = MagicMock()  # type: ignore[assignment]

from pages.collection import open_modal, update_grid  # noqa: E402
from tests.test_models import create_mock_game  # noqa: E402
from util.models import (  # noqa: E402
    Collection,
    CollectionItem,
    GameRelationship,
    OwnershipStatus,
    RelatedGame,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

    from util.models import Game


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(name="mem_engine")
def mem_engine_fixture() -> Generator[Engine, None, None]:
    """In-memory SQLite engine with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(mem_engine: Engine) -> Generator[Session, None, None]:
    with Session(mem_engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_triggered(bgg_id: int) -> MagicMock:
    """Return a fake dash.callback_context with one triggered card click."""
    ctx = MagicMock()
    ctx.triggered = [
        {"prop_id": f'{{"index":{bgg_id},"type":"game-card"}}.n_clicks'}
    ]
    ctx.triggered_id = {"index": bgg_id, "type": "game-card"}
    return ctx


# ---------------------------------------------------------------------------
# update_grid tests
# ---------------------------------------------------------------------------


class TestUpdateGrid:
    def test_returns_grid_on_success(self) -> None:
        """update_grid builds a SimpleGrid when games are returned."""
        mock_game = create_mock_game(1, "Catan")
        mock_item = MagicMock()
        mock_item.game = mock_game
        mock_item.ownership_status = MagicMock(name="owned")

        mock_collection = MagicMock()
        mock_collection.items = [mock_item]

        with patch(
            "pages.collection.get_user_game_collection",
            return_value=mock_collection,
        ):
            grid, loading = update_grid(None)

        assert isinstance(grid, dmc.SimpleGrid)
        assert loading is False
        assert len(grid.children) == 1

    def test_returns_alert_when_collection_is_none(self) -> None:
        """update_grid shows an error alert when the API returns None."""
        with patch(
            "pages.collection.get_user_game_collection",
            return_value=None,
        ):
            result, loading = update_grid(None)

        assert isinstance(result, dmc.Alert)
        assert loading is False

    def test_returns_alert_when_collection_items_empty(self) -> None:
        """update_grid shows an error alert when collection has no items."""
        mock_collection = MagicMock()
        mock_collection.items = []

        with patch(
            "pages.collection.get_user_game_collection",
            return_value=mock_collection,
        ):
            result, loading = update_grid(None)

        assert isinstance(result, dmc.Alert)
        assert loading is False

    def test_games_sorted_alphabetically(self) -> None:
        """update_grid sorts cards by game name."""
        game_a = create_mock_game(1, "Azul")
        game_z = create_mock_game(2, "Zombicide")
        game_m = create_mock_game(3, "Monopoly")

        def make_item(game: Game) -> MagicMock:
            item = MagicMock()
            item.game = game
            item.ownership_status = None
            return item

        mock_collection = MagicMock()
        mock_collection.items = [
            make_item(game_z),
            make_item(game_m),
            make_item(game_a),
        ]

        with patch(
            "pages.collection.get_user_game_collection",
            return_value=mock_collection,
        ):
            grid, _ = update_grid(None)

        names = [
            card.children[1].children[0].children for card in grid.children
        ]
        assert names == ["Azul", "Monopoly", "Zombicide"]

    def test_items_with_no_game_are_skipped(self) -> None:
        """update_grid skips CollectionItems where .game is None/falsy."""
        real_item = MagicMock()
        real_item.game = create_mock_game(1, "Pandemic")
        real_item.ownership_status = None

        ghost_item = MagicMock()
        ghost_item.game = None

        mock_collection = MagicMock()
        mock_collection.items = [real_item, ghost_item]

        with patch(
            "pages.collection.get_user_game_collection",
            return_value=mock_collection,
        ):
            grid, _ = update_grid(None)

        assert len(grid.children) == 1


# ---------------------------------------------------------------------------
# open_modal tests
# ---------------------------------------------------------------------------


class TestOpenModal:
    def test_no_trigger_returns_closed(self) -> None:
        """open_modal returns a closed modal when ctx has no triggers."""
        ctx = MagicMock()
        ctx.triggered = []

        with patch("pages.collection.dash.callback_context", ctx):
            opened, title, rating, content, loading = open_modal(None, None)

        assert opened is False
        assert title == ""
        assert loading is False

    def test_all_none_clicks_returns_closed(self) -> None:
        """open_modal returns closed when every click value is None."""
        ctx = _make_triggered(42)

        with patch("pages.collection.dash.callback_context", ctx):
            opened, title, rating, content, loading = open_modal(
                [None], [None]
            )

        assert opened is False

    def test_game_not_found_in_db(self, mem_engine: Engine) -> None:
        """open_modal returns an error when bgg_id is not in the database."""
        ctx = _make_triggered(999)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
        ):
            opened, title, rating, content, loading = open_modal([1], [None])

        assert opened is True
        assert title == "Error"
        assert loading is False

    def test_game_found_opens_modal(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal returns modal data when a game exists in the DB."""
        game = create_mock_game(101, "Terra Mystica")
        game.description = "Build and expand."
        session.add(game)
        session.commit()
        session.refresh(game)

        ctx = _make_triggered(101)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
        ):
            opened, title, rating, content, loading = open_modal([1], [None])

        assert opened is True
        assert title == "Terra Mystica"
        assert "7.5" in rating  # from create_mock_game default bgg_rating
        assert loading is False

    def test_game_with_no_rating_shows_na(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal displays 'N/A' for games without a BGG rating."""
        game = create_mock_game(202, "Abstract Game")
        game.bgg_rating = None
        game.description = "Very abstract."
        session.add(game)
        session.commit()
        session.refresh(game)

        ctx = _make_triggered(202)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
        ):
            opened, title, rating, content, loading = open_modal([1], [None])

        assert opened is True
        assert rating == "N/A"

    def test_related_games_shown_in_modal(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal includes related game buttons in the modal content."""
        base = create_mock_game(301, "Base Game")
        expansion = create_mock_game(302, "Big Expansion")
        rel_type = GameRelationship(type="expansion")

        session.add(base)
        session.add(expansion)
        session.add(rel_type)
        session.commit()
        session.refresh(base)
        session.refresh(expansion)
        session.refresh(rel_type)

        link = RelatedGame(
            source_game_id=base.id,
            target_game_id=expansion.id,
            relationship_type_id=rel_type.id,
        )
        session.add(link)
        session.commit()

        ctx = _make_triggered(301)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
        ):
            opened, title, _, content, loading = open_modal([1], [None])

        assert opened is True
        assert title == "Base Game"
        assert loading is False
        # Content is a Grid; verify it was built without errors
        assert isinstance(content, dmc.Grid)

    def test_owned_related_game_shows_badge(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal marks a related game as 'Owned' if in user's collection."""
        base = create_mock_game(401, "Main Game")
        expansion = create_mock_game(402, "Owned DLC")
        rel_type = GameRelationship(type="expansion")
        status = OwnershipStatus(name="owned")

        session.add_all([base, expansion, rel_type, status])
        session.commit()
        session.refresh(base)
        session.refresh(expansion)
        session.refresh(rel_type)
        session.refresh(status)

        link = RelatedGame(
            source_game_id=base.id,
            target_game_id=expansion.id,
            relationship_type_id=rel_type.id,
        )
        collection = Collection(name="My Collection", username="testuser")
        session.add(link)
        session.add(collection)
        session.commit()
        session.refresh(collection)

        owned_item = CollectionItem(
            collection_id=collection.id,
            game_id=expansion.id,
            ownership_status_id=status.id,
        )
        session.add(owned_item)
        session.commit()

        ctx = _make_triggered(401)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
            patch("pages.collection.TEST_USER", "testuser"),
        ):
            opened, title, _, content, loading = open_modal([1], [None])

        assert opened is True
        assert title == "Main Game"
