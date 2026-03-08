from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

from api.bgg_api.game_details import (
    _process_and_save_game_details,
    get_game_info,
    save_game_data_to_db,
)
from util.models import Game


@pytest.fixture(name="mem_engine")
def mem_engine_fixture() -> Generator[Engine, None, None]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(autouse=True)
def mock_engine(mem_engine: Engine) -> Generator[None, None, None]:
    with patch("api.bgg_api.game_details.engine", mem_engine):
        yield


def test_process_and_save_item_list_and_empty(mem_engine: Engine) -> None:
    with Session(mem_engine) as session:
        # Test empty item
        g_obj, img = _process_and_save_game_details(session, 1, {"items": {}})
        assert g_obj is None
        assert img is None

        # Test item as list
        data = {
            "items": {
                "item": [
                    {
                        "@id": "2",
                        "name": {"@type": "primary", "@value": "Test2"},
                    }
                ]
            }
        }
        g_obj, img = _process_and_save_game_details(session, 2, data)
        assert g_obj is not None
        assert g_obj.name == "Test2"


def test_process_and_save_no_primary_name_and_dict_links(
    mem_engine: Engine,
) -> None:
    with Session(mem_engine) as session:
        # No primary name + dict links
        data = {
            "items": {
                "item": {
                    "@id": "3",
                    "name": {"@type": "alternate", "@value": "AltName"},
                    "link": {
                        "@type": "boardgamecategory",
                        "@value": "Card Game",
                    },
                }
            }
        }
        g_obj, img = _process_and_save_game_details(session, 3, data)
        assert g_obj is not None
        assert g_obj.name == "AltName"


def test_process_and_save_update_existing_keep_image(
    mem_engine: Engine,
) -> None:
    with Session(mem_engine) as session:
        # Create game first
        game = Game(
            bgg_id=4,
            name="Existing",
            version=1.0,
            description="desc",
            release_year=2000,
            min_players=1,
            max_players=2,
            min_age=10,
            min_play_time=10,
            max_play_time=20,
            image_path="keep_this.jpg",
            recommended_players=None,
            bgg_rating=None,
            bgg_rank=None,
            complexity=None,
        )
        session.add(game)
        session.commit()

        # Update it without wiping image
        data = {
            "items": {
                "item": {
                    "@id": "4",
                    "name": {"@type": "primary", "@value": "Updated"},
                    "image": "new_image.jpg",
                    "description": "desc",
                    "yearpublished": {"@value": "2000"},
                    "minplayers": {"@value": "1"},
                    "maxplayers": {"@value": "2"},
                    "minage": {"@value": "10"},
                    "minplaytime": {"@value": "10"},
                    "maxplaytime": {"@value": "20"},
                }
            }
        }
        g_obj, img = _process_and_save_game_details(session, 4, data)
        assert g_obj is not None
        assert g_obj.name == "Updated"
        assert g_obj.image_path == "keep_this.jpg"


@patch("api.bgg_api.game_details.select")
def test_process_and_save_exception(
    mock_select: MagicMock, mem_engine: Engine
) -> None:
    mock_select.side_effect = Exception("DB Error")
    data = {
        "items": {
            "item": {
                "@id": "5",
                "name": {"@type": "primary", "@value": "ErrorGame"},
            }
        }
    }
    with Session(mem_engine) as session:
        g_obj, img = _process_and_save_game_details(session, 5, data)
        assert g_obj is None
        assert img is None


@patch("api.bgg_api.game_details.get_xml_info")
def test_get_game_info_flags(mock_get_xml: MagicMock) -> None:
    mock_get_xml.return_value = {"success": True}

    # Test all flags as true
    get_game_info(
        game_ids=[10, 20],
        get_stats=True,
        get_versions=True,
        get_videos=True,
        get_comments=True,
        get_marketplacelistings=True,
        get_trading=True,
        get_want=True,
        get_rank=True,
        get_image_list=True,
    )

    args, kwargs = mock_get_xml.call_args
    query = kwargs["query"]
    assert query["stats"] == "1"
    assert query["versions"] == "1"
    assert query["videos"] == "1"
    assert "0" not in query.values()
    assert query["id"] == "10,20"


@patch("api.bgg_api.game_details.get_images")
@patch("api.bgg_api.game_details._process_and_save_game_details")
def test_save_game_data_no_session_and_image(
    mock_process: MagicMock, mock_get_images: MagicMock, mem_engine: Engine
) -> None:
    mock_game = MagicMock()
    mock_process.return_value = (mock_game, "http://download.jpg")
    mock_get_images.return_value = {123: "saved.jpg"}

    game_data = {"@id": "123", "name": "Game To Save"}

    with patch("api.bgg_api.game_details.select"):
        mock_session_exec = MagicMock()
        mock_game_obj = MagicMock()
        mock_session_exec.first.return_value = mock_game_obj
        # Mock the session object's exec
        with patch.object(Session, "exec", return_value=mock_session_exec):
            # This calls save_game_data_to_db with session=None
            save_game_data_to_db(game_data)

            mock_get_images.assert_called_once_with([
                (123, "http://download.jpg")
            ])
            assert mock_game_obj.image_path == "saved.jpg"
