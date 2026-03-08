from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import dash
import dash_mantine_components as dmc
import pytest
from sqlmodel import Session, SQLModel, create_engine

# Must mock register_page before importing the module
dash.register_page = MagicMock()  # type: ignore[assignment, unused-ignore]

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


def _find_badges(component: Any) -> list[dmc.Badge]:
    """Recursively collect all dmc.Badge instances in a component tree."""
    badges: list[dmc.Badge] = []
    if isinstance(component, dmc.Badge):
        badges.append(component)
    children = getattr(component, "children", None)
    if children is None:
        return badges
    if isinstance(children, list):
        for child in children:
            badges.extend(_find_badges(child))
    elif hasattr(children, "children"):  # single component
        badges.extend(_find_badges(children))
    return badges


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
            patch(
                "pages.collection.get_game_info",
                return_value={"items": {"item": {}}},
            ),
            patch("pages.collection.save_game_data_to_db"),
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

    def test_game_with_no_complexity_shows_na(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal displays 'N/A' for games without a complexity rating."""
        game = create_mock_game(203, "Simple Game")
        game.complexity = None
        game.description = "Very simple."
        session.add(game)
        session.commit()
        session.refresh(game)

        ctx = _make_triggered(203)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
        ):
            opened, title, _, content, _ = open_modal([1], [None])

        assert opened is True
        assert title == "Simple Game"

        # Verify 'Weight: N/A' is in the text components
        def _get_texts(component: Any) -> list[str]:
            texts: list[str] = []
            if isinstance(component, dmc.Text):
                texts.append(str(component.children))
            children = getattr(component, "children", None)
            if children is None:
                return texts
            if isinstance(children, list):
                for child in children:
                    texts.extend(_get_texts(child))
            elif hasattr(children, "children"):
                texts.extend(_get_texts(children))
            return texts

        all_text = _get_texts(content)
        # The text might be spread out depending on the UI component structure,
        # but we specifically want to ensure 0.0 or other defaults aren't shown,
        # and that the component successfully rendered despite complexity being None.
        assert not any("0.0/5" in text for text in all_text)
        assert any("N/A" in text for text in all_text), "Expected N/A in texts"

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
        # Walk the full component tree to find all badges and verify one is
        # the green "Owned" badge.
        badges = _find_badges(content)
        assert any(
            b.children == "Owned" and getattr(b, "color", None) == "green"
            for b in badges
        ), "Expected green 'Owned' badge in related game section"

    def test_prevowned_related_game_shows_badge(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal shows a gray 'Prev. Owned' badge for prevowned games."""
        base = create_mock_game(501, "Main Game 2")
        expansion = create_mock_game(502, "Old Expansion")
        rel_type = GameRelationship(type="expansion")
        status = OwnershipStatus(name="prevowned")

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
        collection = Collection(name="My Collection", username="testuser2")
        session.add(link)
        session.add(collection)
        session.commit()
        session.refresh(collection)

        session.add(
            CollectionItem(
                collection_id=collection.id,
                game_id=expansion.id,
                ownership_status_id=status.id,
            )
        )
        session.commit()

        ctx = _make_triggered(501)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
            patch("pages.collection.TEST_USER", "testuser2"),
        ):
            _, title, _, content, _ = open_modal([1], [None])

        assert title == "Main Game 2"
        badges = _find_badges(content)
        assert any(
            b.children == "Prev. Owned" and getattr(b, "color", None) == "gray"
            for b in badges
        ), "Expected gray 'Prev. Owned' badge in related game section"

    def test_want_related_game_shows_no_badge(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal shows no badge when a related game has 'want' status."""
        base = create_mock_game(601, "Main Game 3")
        expansion = create_mock_game(602, "Wished Expansion")
        rel_type = GameRelationship(type="expansion")
        status = OwnershipStatus(name="want")

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
        collection = Collection(name="My Collection", username="testuser3")
        session.add(link)
        session.add(collection)
        session.commit()
        session.refresh(collection)

        session.add(
            CollectionItem(
                collection_id=collection.id,
                game_id=expansion.id,
                ownership_status_id=status.id,
            )
        )
        session.commit()

        ctx = _make_triggered(601)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch("pages.collection.engine", mem_engine),
            patch("pages.collection.TEST_USER", "testuser3"),
        ):
            _, title, _, content, _ = open_modal([1], [None])

        assert title == "Main Game 3"
        badges = _find_badges(content)
        owned_or_prev = [
            b for b in badges if b.children in ("Owned", "Prev. Owned")
        ]
        assert not owned_or_prev, (
            "Expected no ownership badge for 'want' status"
        )
