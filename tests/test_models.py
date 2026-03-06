from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

from util.models import (
    Collection,
    CollectionItem,
    Game,
    GameRelationship,
    OwnershipStatus,
    RelatedGame,
)


@pytest.fixture(name="engine")
def engine_fixture() -> Generator[Engine, None, None]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def test_create_db_and_tables(engine: Engine) -> None:
    # Verify that the tables are created.
    # By default, SQLModel.metadata.tables contains the defined tables
    tables = SQLModel.metadata.tables.keys()
    assert "game" in tables
    assert "collection" in tables
    assert "collectionitem" in tables
    assert "ownershipstatus" in tables
    assert "gamerelationship" in tables
    assert "relatedgame" in tables


def create_mock_game(bgg_id: int, name: str) -> Game:
    return Game(
        bgg_id=bgg_id,
        name=name,
        version=1.0,
        description="A great game",
        release_year=2025,
        min_players=1,
        max_players=4,
        recommended_players=2,
        min_age=10,
        min_play_time=30,
        max_play_time=60,
        bgg_rating=7.5,
        bgg_rank=100,
        complexity=2.5,
    )


def test_game_crud(session: Session) -> None:
    game = create_mock_game(1, "Test Game")
    session.add(game)
    session.commit()
    session.refresh(game)

    assert game.id is not None
    assert game.name == "Test Game"

    # Read
    db_game = session.get(Game, game.id)
    assert db_game is not None
    assert db_game.bgg_id == 1

    # Update
    db_game.name = "Updated Test Game"
    session.add(db_game)
    session.commit()

    db_game_updated = session.get(Game, game.id)
    assert db_game_updated is not None
    assert db_game_updated.name == "Updated Test Game"

    # Delete
    session.delete(db_game_updated)
    session.commit()

    assert session.get(Game, game.id) is None


def test_related_game_crud(session: Session) -> None:
    game1 = create_mock_game(1, "Base Game")
    game2 = create_mock_game(2, "Expansion")

    rel_type = GameRelationship(type="expansion")

    session.add(game1)
    session.add(game2)
    session.add(rel_type)
    session.commit()

    session.refresh(game1)
    session.refresh(game2)
    session.refresh(rel_type)

    related = RelatedGame(
        source_game_id=game1.id,
        target_game_id=game2.id,
        relationship_type_id=rel_type.id,
    )
    session.add(related)
    session.commit()

    # Read
    db_related = session.exec(select(RelatedGame)).first()
    assert db_related is not None
    assert db_related.source_game_id == game1.id
    assert db_related.target_game_id == game2.id

    # Check relationships via Games
    session.refresh(game1)
    assert len(game1.related_to) == 1
    assert game1.related_to[0].bgg_id == 2

    session.refresh(game2)
    assert len(game2.related_from) == 1
    assert game2.related_from[0].bgg_id == 1

    # Delete
    session.delete(db_related)
    session.commit()

    assert session.exec(select(RelatedGame)).first() is None


def test_collection_crud(session: Session) -> None:
    game1 = create_mock_game(1, "Game 1")
    game2 = create_mock_game(2, "Game 2")
    session.add(game1)
    session.add(game2)

    status_owned = OwnershipStatus(name="owned")
    status_want = OwnershipStatus(name="want")
    session.add(status_owned)
    session.add(status_want)
    session.commit()

    # Create Collection
    collection = Collection(name="Test Collection", username="testuser")
    session.add(collection)
    session.commit()
    session.refresh(collection)

    # Add items to collection
    item1 = CollectionItem(
        collection_id=collection.id,
        game_id=game1.id,
        ownership_status_id=status_owned.id,
    )
    item2 = CollectionItem(
        collection_id=collection.id,
        game_id=game2.id,
        ownership_status_id=status_want.id,
    )

    session.add(item1)
    session.add(item2)
    session.commit()

    # Verify collection items
    db_collection = session.exec(
        select(Collection).where(Collection.username == "testuser")
    ).first()
    assert db_collection is not None
    assert len(db_collection.items) == 2

    # Verify relationships
    owned_item = next(
        item for item in db_collection.items if item.game_id == game1.id
    )
    assert owned_item.game.name == "Game 1"
    assert owned_item.ownership_status.name == "owned"

    want_item = next(
        item for item in db_collection.items if item.game_id == game2.id
    )
    assert want_item.game.name == "Game 2"
    assert want_item.ownership_status.name == "want"

    # Delete items explicitly first to prevent NOT NULL constraint fail on primary keys
    for item in db_collection.items:
        session.delete(item)
    session.commit()

    # Delete collection
    session.delete(db_collection)
    session.commit()

    # Verify deletion
    assert session.exec(select(Collection)).first() is None
