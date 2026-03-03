import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from api.bgg_api_interface import _process_and_save_game_details
from util.database.models import (
    Game,
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
    assert len(related_links) == 1

    link = related_links[0]
    target_game = session.get(Game, link.target_game_id)
    assert target_game is not None
    assert target_game.bgg_id == 456


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
