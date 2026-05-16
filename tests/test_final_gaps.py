from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import dash

# Must mock register_page before importing the module
dash.register_page = MagicMock()  # ty:ignore[invalid-assignment]

import dash_mantine_components as dmc  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from pages.collection import (  # noqa: E402
    load_collection_store,
    open_modal,
    render_grid,
    start_sync,
    update_progress,
)
from util.models import Collection, Game  # noqa: E402
from util.status import get_sync_status, set_sync_status  # noqa: E402


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


def test_collection_gaps():
    # Use an in-memory database for real model objects
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Test open_modal gaps
    # Line 317: Modal close
    with patch("dash.callback_context") as mock_ctx:
        mock_ctx.triggered_id = "game-detail-modal"
        mock_ctx.triggered = [{"value": 0}]
        res = open_modal(
            [], [], 0, 0, False, 0, {"history": [], "current_index": -1}
        )
        assert res[0] is False

    # Line 346-360: Back/Forward/Sync
    with patch("dash.callback_context") as mock_ctx:
        mock_ctx.triggered = [{"value": 1, "prop_id": "..."}]

        # Back button
        mock_ctx.triggered_id = "modal-back-button"
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
        with Session(engine) as session:
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
            )  # ty:ignore[missing-argument]
            session.add(game)
            # Add collection for current user
            col = Collection(name="Main", username="phoenix713")
            session.add(col)
            session.commit()

        with (
            patch("pages.collection.engine", engine),
            patch(
                "pages.collection.get_active_username",
                return_value="phoenix713",
            ),
        ):
            res = open_modal(
                [], [], 0, 0, True, 1, {"history": [1], "current_index": 0}
            )
            assert res is not dash.no_update
            assert res[1] == "Test"


def test_start_sync_logic():
    res = start_sync(None)
    assert res[0] is True
    assert res[1] == {"display": "none"}

    with (
        patch("pages.collection.get_active_username", return_value="test"),
        patch("threading.Thread") as mock_thread,
    ):
        res = start_sync(1)
        assert res[0] is False
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


def test_load_collection_store_empty():
    with patch("pages.collection.get_user_game_collection") as mock_get:
        mock_get.return_value = None
        assert load_collection_store(None, 0) == []


def test_render_grid_empty():
    res = render_grid([], 1)
    assert isinstance(res[0], dmc.Alert)
    assert res[2] == {"display": "none"}
