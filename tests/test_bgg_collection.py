from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


import pytest
from sqlmodel import Session, select

from api.bgg_api.collection import (
    get_user_collection_from_db,
    get_user_game_collection,
    save_collection_data_to_db,
    user_exists_in_db,
)
from util.models import Collection, CollectionItem

# Fixtures are now centralized in tests/conftest.py


def test_user_exists_in_db(mem_engine: Engine) -> None:
    with Session(mem_engine) as session:
        collection = Collection(username="testuser", name="test collection")
        session.add(collection)
        session.commit()

    assert user_exists_in_db("testuser") is True
    assert user_exists_in_db("missinguser") is False


def test_get_user_collection_from_db(mem_engine: Engine) -> None:
    with Session(mem_engine) as session:
        collection = Collection(username="testuser2", name="test collection 2")
        session.add(collection)
        session.commit()

    coll = get_user_collection_from_db("testuser2")
    assert coll is not None
    assert coll.username == "testuser2"

    assert get_user_collection_from_db("missinguser2") is None


@patch("api.bgg_api.collection.get_xml_info")
@patch("api.bgg_api.collection.save_collection_data_to_db")
def test_get_user_game_collection_bgg_api_fallback(
    mock_save: MagicMock, mock_get_xml: MagicMock, mem_engine: Engine
) -> None:
    mock_get_xml.return_value = {"items": "fake_data"}
    coll = get_user_game_collection("freshuser")

    mock_get_xml.assert_called_once()
    mock_save.assert_called_once_with("freshuser", {"items": "fake_data"})
    # It attempts to retrieve again from DB, which is empty since we mocked save
    assert coll is None


@patch("api.bgg_api.collection.get_xml_info")
def test_get_user_game_collection_no_data_from_bgg(
    mock_get_xml: MagicMock, mem_engine: Engine
) -> None:
    mock_get_xml.return_value = {}
    coll = get_user_game_collection("freshuser")
    assert coll is None


def test_get_user_game_collection_invalid_filter() -> None:
    with pytest.raises(ValueError, match="Invalid filter"):
        get_user_game_collection("user", filters={"invalid_filter": 1})


def test_get_user_game_collection_invalid_username() -> None:
    assert get_user_game_collection("") is None
    assert get_user_game_collection(None) is None  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
    assert get_user_game_collection("None") is None
    assert get_user_game_collection("null") is None


def test_get_user_game_collection_db_hit(mem_engine: Engine) -> None:
    with Session(mem_engine) as session:
        collection = Collection(username="dbuser", name="db collection")
        session.add(collection)
        session.commit()

    # Should hit DB and not call BGG since force_update is False by default
    with patch("api.bgg_api.collection.get_xml_info") as mock_get_xml:
        coll = get_user_game_collection("dbuser")
        assert coll is not None
        assert coll.username == "dbuser"
        mock_get_xml.assert_not_called()


@patch("api.bgg_api.collection.get_game_info")
@patch("api.bgg_api.collection._process_and_save_game_details")
@patch("api.bgg_api.collection.get_images")
def test_save_collection_data_to_db_full_flow(
    mock_get_images: MagicMock,
    mock_process: MagicMock,
    mock_get_game_info: MagicMock,
    mem_engine: Engine,
) -> None:
    collection_data = {
        "items": {
            "item": {
                "@objectid": "123",
                "status": {"@want": "1"},
            }
        }
    }

    mock_get_game_info.return_value = {"items": {"item": {"@id": "123"}}}

    mock_game = MagicMock()
    mock_game.id = b"uuid"
    mock_game.bgg_id = 123
    mock_get_images.return_value = {123: "saved_image.jpg"}

    from util.models import Game

    with Session(mem_engine) as session:
        real_game = Game(
            bgg_id=123,
            name="Catan",
            version=1.0,
            description="desc",
            release_year=2000,
            min_players=1,
            max_players=2,
            min_age=10,
            min_play_time=10,
            max_play_time=20,
            recommended_players=None,
            bgg_rating=None,
            bgg_rank=None,
            complexity=None,
        )
        session.add(real_game)
        session.commit()
        session.refresh(real_game)

    mock_process.return_value = (real_game, "http://image")

    save_collection_data_to_db("testuser3", collection_data)

    mock_get_game_info.assert_called_once()
    mock_process.assert_called_once()
    mock_get_images.assert_called_once_with([(123, "http://image")])

    with Session(mem_engine) as session:
        coll = session.exec(
            select(Collection).where(Collection.username == "testuser3")
        ).first()
        assert coll is not None
        assert len(coll.items) == 1
        assert coll.items[0].ownership_status.name == "want"

        saved_game = session.exec(
            select(Game).where(Game.bgg_id == 123)
        ).first()
        assert saved_game is not None
        # Verify image_path is updated
        assert saved_game.image_path == "saved_image.jpg"


@patch("api.bgg_api.collection.get_game_info")
def test_save_collection_data_no_games(
    mock_get_game_info: MagicMock, mem_engine: Engine
) -> None:
    collection_data = {"items": {}}
    save_collection_data_to_db("testuser4", collection_data)
    mock_get_game_info.assert_not_called()

    # Missing objectid mapping should skip fetch
    collection_data = {"items": {"item": {"status": {"@want": "1"}}}}
    save_collection_data_to_db("testuser5", collection_data)
    mock_get_game_info.assert_not_called()


@patch("api.bgg_api.collection.get_game_info")
@patch("api.bgg_api.collection._process_and_save_game_details")
@patch("api.bgg_api.collection.get_images")
def test_save_collection_data_prevowned_status(
    mock_get_images: MagicMock,
    mock_process: MagicMock,
    mock_get_game_info: MagicMock,
    mem_engine: Engine,
) -> None:
    collection_data = {
        "items": {
            "item": {
                "@objectid": "456",
                "status": {"@prevowned": "1"},
            }
        }
    }

    mock_get_game_info.return_value = {"items": {"item": {"@id": "456"}}}

    from util.models import Game

    with Session(mem_engine) as session:
        real_game = Game(
            bgg_id=456,
            name="Azul",
            version=1.0,
            description="desc",
            release_year=2000,
            min_players=1,
            max_players=2,
            min_age=10,
            min_play_time=10,
            max_play_time=20,
            recommended_players=None,
            bgg_rating=None,
            bgg_rank=None,
            complexity=None,
        )
        session.add(real_game)
        session.commit()
        session.refresh(real_game)

    mock_process.return_value = (real_game, None)  # No image
    mock_get_images.return_value = {}

    save_collection_data_to_db("testuser6", collection_data)

    with Session(mem_engine) as session:
        coll = session.exec(
            select(Collection).where(Collection.username == "testuser6")
        ).first()
        assert coll is not None
        assert coll.items[0].ownership_status.name == "prevowned"


@patch("api.bgg_api.collection.get_game_info")
@patch("api.bgg_api.collection._process_and_save_game_details")
@patch("api.bgg_api.collection.get_images")
def test_save_collection_data_update_existing_and_missing_game(
    mock_get_images: MagicMock,
    mock_process: MagicMock,
    mock_get_game_info: MagicMock,
    mem_engine: Engine,
) -> None:
    collection_data = {
        "items": {
            "item": [
                {"@objectid": "789", "status": {"@want": "1"}},  # Exists in db
                {
                    "@objectid": "999",
                    "status": {"@want": "1"},
                },  # Missing in db
            ]
        }
    }

    mock_get_game_info.return_value = {"items": {"item": {"@id": "789"}}}

    from util.models import Game, OwnershipStatus

    with Session(mem_engine) as session:
        real_game = Game(
            bgg_id=789,
            name="Test",
            version=1.0,
            description="desc",
            release_year=2000,
            min_players=1,
            max_players=2,
            min_age=10,
            min_play_time=10,
            max_play_time=20,
            recommended_players=None,
            bgg_rating=None,
            bgg_rank=None,
            complexity=None,
        )
        owned_status = OwnershipStatus(name="owned")
        user_col = Collection(username="testuser7", name="test col")
        session.add_all([real_game, owned_status, user_col])
        session.commit()
        session.refresh(real_game)
        session.refresh(owned_status)
        session.refresh(user_col)

        # Add a CollectionItem with 'owned' status initially
        col_item = CollectionItem(
            collection_id=user_col.id,
            game_id=real_game.id,
            ownership_status_id=owned_status.id,
        )
        session.add(col_item)
        session.commit()

    # Process only returns the real game
    mock_process.return_value = (real_game, None)
    mock_get_images.return_value = {}

    save_collection_data_to_db("testuser7", collection_data)

    with Session(mem_engine) as session:
        coll = session.exec(
            select(Collection).where(Collection.username == "testuser7")
        ).first()
        assert coll is not None
        # Should now be updated to "want" (because it was set to want in collection_data)
        item = session.exec(
            select(CollectionItem).where(
                CollectionItem.collection_id == coll.id
            )
        ).first()
        assert item is not None
        assert item.ownership_status.name == "want"
