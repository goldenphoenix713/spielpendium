from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import dash

# Must mock register_page before importing the module
dash.register_page = MagicMock()  # ty:ignore[invalid-assignment]

import dash_mantine_components as dmc  # noqa: E402
from sqlmodel import Session  # noqa: E402

from pages.collection import (  # noqa: E402
    load_collection_store,
    open_modal,
    render_grid,
    start_sync,
    update_progress,
)

# Import all models to ensure they are in metadata
from util.models import (  # noqa: E402
    Category,
    Collection,
    CollectionItem,
    Game,
    GameCategoryLink,
    GameRelationship,
    OwnershipStatus,
    PersonGameLink,
    PersonRole,
    Publisher,
    PublisherGameLink,
    RelatedGame,
    Search,
    UserSettings,
)
from util.status import get_sync_status, set_sync_status  # noqa: E402

# Explicitly reference unused models to satisfy all linters and ensure they stay in metadata
_unused_models = [
    Category,
    CollectionItem,
    GameCategoryLink,
    GameRelationship,
    OwnershipStatus,
    PersonGameLink,
    PersonRole,
    Publisher,
    PublisherGameLink,
    RelatedGame,
    Search,
    UserSettings,
]


# Fixtures are now centralized in tests/conftest.py


def test_directories_env_override():
    with patch.dict(os.environ, {"DB_FILE": "test_db.sqlite"}):
        pass


def test_sync_status():
    set_sync_status(True, 1, 10, "Syncing...")
    status = get_sync_status()
    assert status.active is True
    assert status.current == 1
    assert status.total == 10
    assert status.message == "Syncing..."


def test_collection_gaps(mem_engine):
    # Patch everything globally for this test
    with (
        patch("pages.collection.engine", mem_engine),
        patch("util.settings.engine", mem_engine),
        patch(
            "pages.collection.get_active_username", return_value="phoenix713"
        ),
        patch("pages.collection.get_game_info") as mock_info,
        patch("pages.collection.save_game_data_to_db"),
        patch("dash.callback_context") as mock_ctx,
    ):
        # Mock API return value
        mock_info.return_value = {
            "items": {"item": {"name": "Mock", "description": "Mock"}}
        }

        # Line 317: Modal close
        mock_ctx.triggered_id = "game-detail-modal"
        mock_ctx.triggered = [{"value": 0}]
        res = open_modal(
            [], [], 0, 0, False, 0, {"history": [], "current_index": -1}
        )
        assert res[0] is False

        # Line 346-360: Back/Forward/Sync
        mock_ctx.triggered = [{"value": 1, "prop_id": "..."}]

        # Back button
        mock_ctx.triggered_id = "modal-back-button"
        # Even if not in DB, it will now use the mock_info
        res = open_modal(
            [], [], 1, 0, True, 0, {"history": [1, 2], "current_index": 1}
        )
        assert res[6]["current_index"] == 0

        # Forward button
        mock_ctx.triggered_id = "modal-forward-button"
        res = open_modal(
            [], [], 0, 1, True, 0, {"history": [1, 2], "current_index": 0}
        )
        assert res[6]["current_index"] == 1

        # Sync game button
        mock_ctx.triggered_id = "sync-game-btn"

        # Create a real game in the DB
        with Session(mem_engine) as session:
            game = Game(
                bgg_id=1,
                name="Test",
                description="Desc",
                complexity=2.5,
                release_year=2020,
                min_players=1,
                max_players=4,
                min_play_time=30,
                max_play_time=60,
                version=1.0,
                min_age=10,
                recommended_players=None,
                bgg_rating=None,
                bgg_rank=None,
            )
            session.add(game)
            # Add collection for current user
            col = Collection(name="Main", username="phoenix713")
            session.add(col)
            session.commit()

        # Call open_modal which will now find the game in our mem_engine
        res = open_modal(
            [], [], 0, 0, True, 1, {"history": [1], "current_index": 0}
        )
        assert res is not dash.no_update
        assert res[1] == "Test"


def test_start_sync_logic():
    res = start_sync(None, None)
    assert res == dash.no_update

    with (
        patch("threading.Thread") as mock_thread,
    ):
        res = start_sync(1, "test")
        assert res[0] is False
        assert res[1] == {"display": "block"}
        assert res[2] is True
        assert mock_thread.called


def test_update_progress_logic():
    set_sync_status(False, message="Done")
    res = update_progress(0, 0)
    assert res[0] == 100
    assert res[2] == "Done"

    set_sync_status(True, current=5, total=10, message="Running")
    res = update_progress(0, 0)
    assert res[0] == 50
    assert res[2] == "Running"


def test_load_collection_store_empty(mem_engine):
    with (
        patch("pages.collection.get_user_game_collection") as mock_get,
        patch("util.settings.engine", mem_engine),
        patch(
            "pages.collection.get_active_username", return_value="phoenix713"
        ),
    ):
        mock_get.return_value = None
        assert load_collection_store(0, "phoenix713") == []


def test_render_grid_empty():
    res = render_grid([], 1, "testuser")
    assert isinstance(res[0], dmc.Alert)
    assert res[2] == {"display": "none"}
