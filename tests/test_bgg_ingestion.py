from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from api.bgg_api_interface import (
    _process_and_save_game_details,
    save_collection_data_to_db,
)
from util.models import (
    Collection,
    Game,
    GameRelationship,
    RelatedGame,
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_process_and_save_game_details_basic(session: Session):
    # Mock BGG API response structure for a single game (Thing endpoint)
    mock_bgg_data = {
        "items": {
            "item": {
                "@id": "123",
                "name": {"@type": "primary", "@value": "Test Game"},
                "description": "A test game description.",
                "yearpublished": {"@value": "2024"},
                "minplayers": {"@value": "2"},
                "maxplayers": {"@value": "4"},
                "minage": {"@value": "10"},
                "minplaytime": {"@value": "30"},
                "maxplaytime": {"@value": "60"},
                "statistics": {
                    "ratings": {
                        "average": {"@value": "7.5"},
                        "averageweight": {"@value": "2.5"},
                        "ranks": {
                            "rank": {"@name": "boardgame", "@value": "100"}
                        },
                    }
                },
                "boardgamecategory": {"@value": "Fantasy", "@id": "1010"},
                "boardgamepublisher": {
                    "@value": "Test Publisher",
                    "@id": "2020",
                },
                "boardgamedesigner": {
                    "@value": "Test Designer",
                    "@id": "3030",
                },
                "boardgameartist": {"@value": "Test Artist", "@id": "4040"},
                "boardgameexpansion": {
                    "@value": "Test Expansion",
                    "@objectid": "456",
                },
                "boardgamereimplementation": {
                    "@value": "Test Reimplementation",
                    "@objectid": "789",
                },
            }
        }
    }

    game = _process_and_save_game_details(session, 123, mock_bgg_data)
    assert game is not None
    assert game.name == "Test Game"
    assert game.bgg_id == 123
    assert game.release_year == 2024
    assert game.bgg_rating == 7.5
    assert game.bgg_rank == 100

    # Check relationships
    assert len(game.categories) == 1
    assert game.categories[0].name == "Fantasy"

    assert len(game.publishers) == 1
    assert game.publishers[0].name == "Test Publisher"

    assert len(game.authors) == 1
    assert game.authors[0].name == "Test Designer"

    assert len(game.artists) == 1
    assert game.artists[0].name == "Test Artist"

    # Check RelatedGame entry
    related_links = session.exec(
        select(RelatedGame).where(RelatedGame.source_game_id == game.id)
    ).all()
    assert len(related_links) == 2

    # Verify types
    expansion_link = next(
        link
        for link in related_links
        if session.get(GameRelationship, link.relationship_type_id).type
        == "expansion"
    )
    reimp_link = next(
        link
        for link in related_links
        if session.get(GameRelationship, link.relationship_type_id).type
        == "reimplementation"
    )

    assert session.get(Game, expansion_link.target_game_id).bgg_id == 456
    assert session.get(Game, reimp_link.target_game_id).bgg_id == 789


def test_process_and_save_game_details_with_images(session: Session):
    mock_bgg_data = {
        "items": {
            "item": {
                "@id": "123",
                "name": {"@type": "primary", "@value": "Image Test Game"},
                "image": "http://example.com/image.jpg",
                "statistics": {
                    "ratings": {
                        "average": {"@value": "5.0"},
                        "averageweight": {"@value": "2.0"},
                        "ranks": {
                            "rank": {"@name": "boardgame", "@value": "1"}
                        },
                    }
                },
            }
        }
    }

    mock_image_content = b"fake-image-binary-data"

    with patch("requests.Session.get") as mock_get:
        # Configure mock to return different content based on URL
        def side_effect(url, **kwargs):
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.content = mock_image_content
            return mock_res

        mock_get.side_effect = side_effect

        game = _process_and_save_game_details(session, 123, mock_bgg_data)

        assert game.image == mock_image_content


def test_save_collection_data_to_db_full_flow(session: Session):
    # Patch the global engine in the module to use our in-memory test engine
    with patch("api.bgg_api_interface.engine", session.get_bind()):
        username = "test_user"
        mock_collection_data = {
            "items": {
                "item": [
                    {
                        "@objectid": "101",
                        "status": {
                            "@own": "1",
                            "@prevowned": "0",
                            "@want": "0",
                        },
                    },
                    {
                        "@objectid": "102",
                        "status": {
                            "@own": "0",
                            "@prevowned": "0",
                            "@want": "1",
                        },
                    },
                ]
            }
        }

        # Mock game info response for the missing games
        mock_game_details = {
            "items": {
                "item": [
                    {
                        "@id": "101",
                        "name": {"@type": "primary", "@value": "Owned Game"},
                        "description": "Description 101",
                        "yearpublished": {"@value": "2020"},
                        "statistics": {
                            "ratings": {
                                "average": {"@value": "8.5"},
                                "averageweight": {"@value": "3.0"},
                                "ranks": {
                                    "rank": {
                                        "@name": "boardgame",
                                        "@value": "50",
                                    }
                                },
                            }
                        },
                    },
                    {
                        "@id": "102",
                        "name": {"@type": "primary", "@value": "Wanted Game"},
                        "description": "Description 102",
                        "yearpublished": {"@value": "2021"},
                        "statistics": {
                            "ratings": {
                                "average": {"@value": "7.5"},
                                "averageweight": {"@value": "2.5"},
                                "ranks": {
                                    "rank": {
                                        "@name": "boardgame",
                                        "@value": "150",
                                    }
                                },
                            }
                        },
                    },
                ]
            }
        }

        with patch("api.bgg_api_interface.get_game_info") as mock_get_info:
            mock_get_info.return_value = mock_game_details

            # Run the sync logic
            save_collection_data_to_db(username, mock_collection_data)

        # Verify games were created
        games = session.exec(select(Game).order_by(Game.bgg_id)).all()
        assert len(games) == 2
        assert games[0].bgg_id == 101
        assert games[0].name == "Owned Game"
        assert games[1].bgg_id == 102
        assert games[1].name == "Wanted Game"

        # Verify collection was created
        collection = session.exec(
            select(Collection).where(Collection.username == username)
        ).first()
        assert collection is not None
        assert len(collection.items) == 2

        # Verify Ownership statuses
        owned_item = next(i for i in collection.items if i.game.bgg_id == 101)
        assert owned_item.ownership_status.name == "owned"

        wanted_item = next(i for i in collection.items if i.game.bgg_id == 102)
        assert wanted_item.ownership_status.name == "want"


def test_process_and_save_game_details_not_ranked(session: Session):
    mock_bgg_data = {
        "items": {
            "item": {
                "@id": "999",
                "name": {"@type": "primary", "@value": "Unranked Game"},
                "statistics": {
                    "ratings": {
                        "average": {"@value": "0.0"},
                        "averageweight": {"@value": "0.0"},
                        "ranks": {
                            "rank": {
                                "@name": "boardgame",
                                "@value": "Not Ranked",
                            }
                        },
                    }
                },
            }
        }
    }

    game = _process_and_save_game_details(session, 999, mock_bgg_data)
    assert game.bgg_rank is None


def test_process_and_save_game_details_multiple_names(session: Session):
    mock_bgg_data = {
        "items": {
            "item": {
                "@id": "111",
                "name": [
                    {"@type": "primary", "@value": "Primary Name"},
                    {"@type": "alternate", "@value": "Alternate Name"},
                ],
                "yearpublished": {"@value": "2020"},
            }
        }
    }

    game = _process_and_save_game_details(session, 111, mock_bgg_data)
    assert game.name == "Primary Name"
    assert game.sub_name == "Alternate Name"
