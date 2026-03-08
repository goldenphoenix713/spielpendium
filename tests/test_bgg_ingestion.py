from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, col, create_engine, select

if TYPE_CHECKING:
    from collections.abc import Generator

from api.bgg_api.collection import save_collection_data_to_db
from api.bgg_api.game_details import _process_and_save_game_details
from util.models import (
    Collection,
    Game,
    GameRelationship,
    RelatedGame,
)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_process_and_save_game_details_basic(session: Session) -> None:
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
                "link": [
                    {
                        "@type": "boardgamecategory",
                        "@value": "Fantasy",
                        "@id": "1010",
                    },
                    {
                        "@type": "boardgamepublisher",
                        "@value": "Test Publisher",
                        "@id": "2020",
                    },
                    {
                        "@type": "boardgamedesigner",
                        "@value": "Test Designer",
                        "@id": "3030",
                    },
                    {
                        "@type": "boardgameartist",
                        "@value": "Test Artist",
                        "@id": "4040",
                    },
                    {
                        "@type": "boardgameexpansion",
                        "@value": "Test Expansion",
                        "@id": "456",
                    },
                    {
                        "@type": "boardgamereimplementation",
                        "@value": "Test Reimplementation",
                        "@id": "789",
                    },
                ],
            }
        }
    }

    game, _ = _process_and_save_game_details(session, 123, mock_bgg_data)
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
        if (rel := session.get(GameRelationship, link.relationship_type_id))
        is not None
        and rel.type == "boardgameexpansion"
    )
    reimp_link = next(
        link
        for link in related_links
        if (rel := session.get(GameRelationship, link.relationship_type_id))
        is not None
        and rel.type == "boardgamereimplementation"
    )

    game_exp = session.get(Game, expansion_link.target_game_id)
    assert game_exp is not None
    assert game_exp.bgg_id == 456

    game_reimp = session.get(Game, reimp_link.target_game_id)
    assert game_reimp is not None
    assert game_reimp.bgg_id == 789


def test_process_and_save_game_details_with_images(session: Session) -> None:
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
        def side_effect(url: str, **kwargs: Any) -> MagicMock:
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.content = mock_image_content
            return mock_res

        mock_get.side_effect = side_effect

        game, _ = _process_and_save_game_details(session, 123, mock_bgg_data)
    session.commit()

    assert game is not None

    # We will remove the image assertion in a bit, as _process_and_save_game_details won't set image_path anymore


def test_save_collection_data_to_db_full_flow(session: Session) -> None:
    # Patch the global engine in the module to use our in-memory test engine
    with patch("api.bgg_api.collection.engine", session.get_bind()):
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

        with patch("api.bgg_api.collection.get_game_info") as mock_get_info:
            mock_get_info.return_value = mock_game_details

            # Run the sync logic
            save_collection_data_to_db(username, mock_collection_data)

        # Verify games were created
        games = session.exec(select(Game).order_by(col(Game.bgg_id))).all()
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


def test_process_and_save_game_details_not_ranked(session: Session) -> None:
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

    game, _ = _process_and_save_game_details(session, 999, mock_bgg_data)
    assert game is not None
    assert game.bgg_rank is None


def test_process_and_save_game_details_multiple_names(
    session: Session,
) -> None:
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

    game, _ = _process_and_save_game_details(session, 111, mock_bgg_data)
    assert game is not None
    assert game.name == "Primary Name"
    assert game.sub_name == "Alternate Name"


def test_save_game_data_to_db(session: Session) -> None:
    mock_game_data = {
        "@id": "555",
        "name": {"@type": "primary", "@value": "Test Single Save"},
        "description": "A single game save test.",
        "yearpublished": {"@value": "2025"},
        "minplayers": {"@value": "1"},
        "maxplayers": {"@value": "2"},
        "minage": {"@value": "14"},
        "minplaytime": {"@value": "45"},
        "maxplaytime": {"@value": "90"},
        "statistics": {
            "ratings": {
                "average": {"@value": "8.0"},
                "averageweight": {"@value": "3.5"},
                "ranks": {"rank": {"@name": "boardgame", "@value": "42"}},
            }
        },
    }

    # Use the injected test session
    from api.bgg_api.game_details import save_game_data_to_db

    save_game_data_to_db(mock_game_data, session=session)

    # Verify it was saved to the DB
    game = session.exec(select(Game).where(Game.bgg_id == 555)).first()
    assert game is not None
    assert game.name == "Test Single Save"
    assert game.complexity == 3.5


def test_save_game_data_to_db_no_complexity_gracefully_handles(
    session: Session,
) -> None:
    # A game (like an accessory) missing the complexity rating entirely
    mock_game_data = {
        "@id": "666",
        "name": {"@type": "primary", "@value": "Test Accessory Save"},
        "description": "A shiny new accessory.",
        "statistics": {
            "ratings": {
                "average": {"@value": "0.0"},
                # 'averageweight' omitted
            }
        },
    }

    from api.bgg_api.game_details import save_game_data_to_db

    save_game_data_to_db(mock_game_data, session=session)

    # Verify it was saved to the DB with None complexity
    game = session.exec(select(Game).where(Game.bgg_id == 666)).first()
    assert game is not None
    assert game.name == "Test Accessory Save"
    assert game.complexity is None
