from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import dash
import dash_mantine_components as dmc
from dash import html

# Must mock register_page before importing the module
dash.register_page = MagicMock()  # type: ignore[assignment, unused-ignore]  # ty: ignore[invalid-assignment]

from pages.collection import (  # noqa: E402
    filter_collection,
    open_modal,
    render_grid,
)
from tests.test_models import create_mock_game  # noqa: E402
from util.models import (  # noqa: E402
    Collection,
    CollectionItem,
    GameRelationship,
    OwnershipStatus,
    RelatedGame,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlmodel import Session


# ---------------------------------------------------------------------------
# Fixtures are now centralized in tests/conftest.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_triggered(bgg_id: int) -> MagicMock:
    """Return a fake dash.callback_context with one triggered card click."""
    ctx = MagicMock()
    ctx.triggered = [
        {
            "prop_id": f'{{"index":{bgg_id},"type":"game-card"}}.n_clicks',
            "value": 1,
        }
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


# ---------------------------------------------------------------------------
# Default filter/sort args for update_grid ("no filter" state)
# ---------------------------------------------------------------------------
_DEFAULT_FILTERS: dict[str, Any] = {
    "sort_by": "name",
    "sort_dir": "asc",
    "name": "",
    "players": [1, 10],
    "play_time": [0, 300],
    "complexity": [1.0, 5.0],
    "bgg_rating": [1.0, 10.0],
    "bgg_rank_max": None,
    "year": [1900, 2100],
    "categories": [],
    "ownership": [],  # empty = show all statuses
}


class TestGridCallbacks:
    def _make_game_dict(self, bgg_id: int, name: str, **kwargs: Any) -> dict:
        """Build a minimal serialized game dict for use in update_grid tests."""
        return {
            "bgg_id": bgg_id,
            "name": name,
            "image_path": None,
            "bgg_rating": kwargs.get("bgg_rating", 7.5),
            "bgg_rank": kwargs.get("bgg_rank", 100),
            "min_players": kwargs.get("min_players", 2),
            "max_players": kwargs.get("max_players", 4),
            "min_play_time": kwargs.get("min_play_time", 60),
            "max_play_time": kwargs.get("max_play_time", 120),
            "complexity": kwargs.get("complexity", 2.5),
            "release_year": kwargs.get("release_year", 2010),
            "min_age": kwargs.get("min_age", 10),
            "categories": kwargs.get("categories", []),
            "authors": kwargs.get("authors", []),
            "publishers": kwargs.get("publishers", []),
            "ownership_status": kwargs.get("ownership_status", "owned"),
            "statuses": kwargs.get("statuses", []),
        }

    def test_returns_grid_on_success(self) -> None:
        """update_grid builds a SimpleGrid when games are supplied."""
        games = [self._make_game_dict(1, "Catan")]
        filtered, count, page, total_pages = filter_collection(
            games, _DEFAULT_FILTERS
        )
        grid, loading, _ = render_grid(filtered, 1, "testuser")

        assert isinstance(grid, dmc.SimpleGrid)
        assert loading is False
        assert len(grid.children) == 1
        assert "1 of 1" in count

    def test_returns_alert_when_games_none(self) -> None:
        """update_grid shows an error alert when no games are in the store."""
        filtered, count, page, total_pages = filter_collection(
            None, _DEFAULT_FILTERS
        )
        assert filtered == []

        grid, loading, _ = render_grid(filtered, 1, "testuser")
        assert isinstance(grid, dmc.Alert)
        assert loading is False

    def test_returns_alert_when_games_empty(self) -> None:
        """update_grid shows an error alert when store has empty list."""
        filtered, count, page, total_pages = filter_collection(
            [], _DEFAULT_FILTERS
        )
        assert filtered == []

        grid, loading, _ = render_grid(filtered, 1, "testuser")
        assert isinstance(grid, dmc.Alert)
        assert loading is False

    def test_games_sorted_alphabetically(self) -> None:
        """update_grid sorts cards by game name by default."""
        games = [
            self._make_game_dict(1, "Zombicide"),
            self._make_game_dict(2, "Azul"),
            self._make_game_dict(3, "Monopoly"),
        ]
        filtered, _, _, _ = filter_collection(games, _DEFAULT_FILTERS)
        grid, _, _ = render_grid(filtered, 1, "testuser")

        names = [
            card.children.children[1].children.children
            for card in grid.children
        ]
        assert names == ["Azul", "Monopoly", "Zombicide"]

    def test_name_filter(self) -> None:
        """update_grid filters games by name substring."""
        games = [
            self._make_game_dict(1, "Pandemic"),
            self._make_game_dict(2, "Catan"),
        ]
        filters = {**_DEFAULT_FILTERS, "name": "catan"}
        filtered, count, _, _ = filter_collection(games, filters)
        grid, _, _ = render_grid(filtered, 1, "testuser")

        assert isinstance(grid, dmc.SimpleGrid)
        assert len(grid.children) == 1
        assert "1 of 2" in count

    def test_no_match_returns_yellow_alert(self) -> None:
        """update_grid returns a yellow 'No Results' alert when nothing matches."""
        games = [self._make_game_dict(1, "Pandemic")]
        filters = {**_DEFAULT_FILTERS, "name": "zzznomatch"}
        filtered, count, _, _ = filter_collection(games, filters)
        alert, _, _ = render_grid(filtered, 1, "testuser")

        assert isinstance(alert, dmc.Alert)
        assert getattr(alert, "color", None) == "yellow"
        assert "0 of 1" in count

    def test_ownership_filter(self) -> None:
        """update_grid filters games by ownership status."""
        games = [
            self._make_game_dict(1, "Pandemic", statuses=["own"]),
            self._make_game_dict(2, "Catan", statuses=["prevowned"]),
            self._make_game_dict(3, "Azul", statuses=["want"]),
        ]
        filters = {**_DEFAULT_FILTERS, "ownership": ["owned"]}
        filtered, count, _, _ = filter_collection(games, filters)
        grid, _, _ = render_grid(filtered, 1, "testuser")

        assert isinstance(grid, dmc.SimpleGrid)
        assert len(grid.children) == 1
        assert "1 of 3" in count


# ---------------------------------------------------------------------------
# open_modal tests
# ---------------------------------------------------------------------------


class TestOpenModal:
    def test_no_trigger_returns_closed(self) -> None:
        """open_modal returns a closed modal when ctx has no triggers."""
        ctx = MagicMock()
        ctx.triggered = []

        with patch("pages.collection.dash.callback_context", ctx):
            result = open_modal(
                None,
                None,
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        assert result == dash.no_update

    def test_all_none_clicks_returns_closed(self) -> None:
        """open_modal returns closed when every click value is None."""
        ctx = _make_triggered(42)
        ctx.triggered[0]["value"] = None

        with patch("pages.collection.dash.callback_context", ctx):
            result = open_modal(
                [None],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        assert result == dash.no_update

    def test_game_not_found_in_db(self, mem_engine: Engine) -> None:
        """open_modal returns an error when bgg_id is not in the database."""
        ctx = _make_triggered(999)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch(
                "pages.collection.get_game_info",
                return_value={"items": {"item": {}}},
            ),
            patch("pages.collection.save_game_data_to_db"),
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        (
            opened,
            title,
            rating,
            content,
            bgg_link,
            loading,
            history,
            back,
            forward,
        ) = result
        assert opened is True
        assert title == "Error"
        assert loading == dash.no_update

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
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        (
            opened,
            title,
            rating,
            content,
            bgg_link,
            loading,
            history,
            back,
            forward,
        ) = result
        assert opened is True
        assert title == "Terra Mystica"
        assert "7.5" in rating  # from create_mock_game default bgg_rating
        assert loading == dash.no_update

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
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        (
            opened,
            title,
            rating,
            content,
            bgg_link,
            loading,
            history,
            back,
            forward,
        ) = result
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
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        opened, title, _, content, _, _, _, _, _ = result
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
        assert not any("0.0/5" in text for text in all_text)
        assert any("N/A" in text for text in all_text), "Expected N/A in texts"

    def test_related_games_shown_in_modal(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal includes related game buttons in the modal content."""
        base = create_mock_game(301, "Base Game")
        expansion = create_mock_game(302, "Big Expansion")
        rel_type = GameRelationship(type="boardgameexpansion")

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
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        opened, title, _, content, _, loading, _, _, _ = result
        assert opened is True
        assert title == "Base Game"
        assert loading == dash.no_update
        # Content is a Div wrapping a Grid; verify it was built without errors
        assert isinstance(content, html.Div)

    def test_owned_related_game_shows_badge(
        self, session: Session, mem_engine: Engine
    ) -> None:
        """open_modal marks a related game as 'Owned' if in user's collection."""
        base = create_mock_game(401, "Main Game")
        expansion = create_mock_game(402, "Owned DLC")
        rel_type = GameRelationship(type="boardgameexpansion")
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
            statuses=["own"],
        )
        session.add(owned_item)
        session.commit()

        ctx = _make_triggered(401)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch(
                "pages.collection.get_active_username", return_value="testuser"
            ),
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        opened, title, _, content, _, loading, _, _, _ = result
        assert opened is True
        assert title == "Main Game"
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
        rel_type = GameRelationship(type="boardgameexpansion")
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
                statuses=["prevowned"],
            )
        )
        session.commit()

        ctx = _make_triggered(501)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch(
                "pages.collection.get_active_username",
                return_value="testuser2",
            ),
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        _, title, _, content, _, _, _, _, _ = result
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
        rel_type = GameRelationship(type="boardgameexpansion")
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
                statuses=["want"],
            )
        )
        session.commit()

        ctx = _make_triggered(601)

        with (
            patch("pages.collection.dash.callback_context", ctx),
            patch(
                "pages.collection.get_active_username",
                return_value="testuser3",
            ),
        ):
            result = open_modal(
                [1],
                [None],
                None,
                None,
                False,
                None,
                {"history": [], "current_index": -1},
            )

        _, title, _, content, _, _, _, _, _ = result
        assert title == "Main Game 3"
        badges = _find_badges(content)
        owned_or_prev = [
            b for b in badges if b.children in ("Owned", "Prev. Owned")
        ]
        assert not owned_or_prev, (
            "Expected no ownership badge for 'want' status"
        )
