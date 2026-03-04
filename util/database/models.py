import os  # Added import for os
from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4  # noqa: TC003

from sqlalchemy.types import BINARY
from sqlmodel import (
    Field,
    Relationship,
    Session,
    SQLModel,
    create_engine,
)

from config import DB_FILE, DEBUG

__author__ = "Eduardo Ruiz"

__all__ = [
    "GameSearchLink",
    "RelatedGame",
    "GameCategoryLink",
    "PersonGameLink",
    "CollectionItem",
    "PublisherGameLink",
    "Collection",
    "Publisher",
    "Search",
    "GameRelationship",
    "OwnershipStatus",
    "Person",
    "PersonRole",
    "Category",
    "Game",
    "UserSettings",
    "engine",
    "create_db_and_tables",
]


# Define a custom Field for UUIDs to simplify
# We create a function to generate a Field with BLOB(16)
def BinaryUUIDField(**kwargs: Any) -> Any:  # noqa: N802
    return Field(  # type: ignore
        default_factory=lambda: uuid4().bytes,
        sa_type=BINARY(16),
        **kwargs,
    )


# --- LINK MODELS ---


class GameSearchLink(SQLModel, table=True):
    game_id: bytes = BinaryUUIDField(
        foreign_key="game.id", primary_key=True, repr=False
    )
    search_id: bytes = BinaryUUIDField(
        foreign_key="search.id", primary_key=True, repr=False
    )


class RelatedGame(SQLModel, table=True):
    """
    Self-referential link for games.
    E.g., Game A is an expansion of Game B.
    """

    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    source_game_id: bytes = BinaryUUIDField(foreign_key="game.id", repr=False)
    target_game_id: bytes = BinaryUUIDField(foreign_key="game.id", repr=False)
    relationship_type_id: bytes = BinaryUUIDField(
        foreign_key="gamerelationship.id", repr=False
    )
    relationship_type: "GameRelationship" = Relationship(  # noqa:UP037
        back_populates="related_games_link"
    )


class GameCategoryLink(SQLModel, table=True):
    category_id: bytes = BinaryUUIDField(
        foreign_key="category.id", primary_key=True, repr=False
    )
    game_id: bytes = BinaryUUIDField(
        foreign_key="game.id", primary_key=True, repr=False
    )


class PersonGameLink(SQLModel, table=True):
    person_id: bytes = BinaryUUIDField(
        foreign_key="person.id", primary_key=True, repr=False
    )
    game_id: bytes = BinaryUUIDField(
        foreign_key="game.id", primary_key=True, repr=False
    )
    role_id: bytes = BinaryUUIDField(
        foreign_key="personrole.id", primary_key=True, repr=False
    )
    person_role: "PersonRole" = Relationship(  # noqa:UP037
        back_populates="person_game_links"
    )


class CollectionItem(SQLModel, table=True):
    collection_id: bytes = BinaryUUIDField(
        foreign_key="collection.id", primary_key=True, repr=False
    )
    game_id: bytes = BinaryUUIDField(
        foreign_key="game.id", primary_key=True, repr=False
    )
    ownership_status_id: bytes = BinaryUUIDField(
        foreign_key="ownershipstatus.id", repr=False
    )
    collection: "Collection" = Relationship(back_populates="items")  # noqa:UP037
    game: "Game" = Relationship(back_populates="collection_items")  # noqa:UP037
    ownership_status: "OwnershipStatus" = Relationship(  # noqa:UP037
        back_populates="collection_items"
    )


class PublisherGameLink(SQLModel, table=True):
    publisher_id: bytes = BinaryUUIDField(
        foreign_key="publisher.id", primary_key=True, repr=False
    )
    game_id: bytes = BinaryUUIDField(
        foreign_key="game.id", primary_key=True, repr=False
    )


# --- MAIN MODELS ---


class Collection(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    username: str
    name: str
    items: list[CollectionItem] = Relationship(back_populates="collection")


class Publisher(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    name: str
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="publishers", link_model=PublisherGameLink
    )


class Search(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    query: str
    date_time: datetime
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="searches", link_model=GameSearchLink
    )


class GameRelationship(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    type: str  # e.g., "expansion", "reimplementation", "accessory"
    related_games_link: list[RelatedGame] = Relationship(
        back_populates="relationship_type"
    )


class OwnershipStatus(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    name: str
    collection_items: list[CollectionItem] = Relationship(
        back_populates="ownership_status"
    )


class Person(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    name: str
    games_illustrated: list["Game"] = Relationship(  # noqa:UP037
        back_populates="artists",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Person.id==PersonGameLink.person_id",
            "secondaryjoin": "and_(Game.id==PersonGameLink.game_id, PersonGameLink.role_id==select(PersonRole.id).where(PersonRole.role=='artist').scalar_subquery())",
            "overlaps": "games_authored",
        },
    )
    games_authored: list["Game"] = Relationship(  # noqa:UP037
        back_populates="authors",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Person.id==PersonGameLink.person_id",
            "secondaryjoin": "and_(Game.id==PersonGameLink.game_id, PersonGameLink.role_id==select(PersonRole.id).where(PersonRole.role=='author').scalar_subquery())",
            "overlaps": "games_illustrated",
        },
    )


class PersonRole(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    role: str
    person_game_links: list[PersonGameLink] = Relationship(
        back_populates="person_role"
    )


class Category(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    name: str
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="categories", link_model=GameCategoryLink
    )


class Game(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    bgg_id: int = Field(
        unique=True, index=True, nullable=False
    )  # New field for BGG ID
    name: str
    sub_name: str | None = None
    version: float
    image: bytes | None = Field(default=None, repr=False)
    thumbnail: bytes | None = Field(default=None, repr=False)
    description: str = Field(repr=False)
    release_year: int = Field(repr=False)
    min_players: int = Field(repr=False)
    max_players: int = Field(repr=False)
    recommended_players: int | None = Field(repr=False)
    min_age: int = Field(repr=False)
    min_play_time: int = Field(repr=False)
    max_play_time: int = Field(repr=False)
    bgg_rating: float | None = Field(repr=False)
    bgg_rank: int | None = Field(repr=False)
    complexity: float = Field(repr=False)
    publishers: list[Publisher] = Relationship(
        back_populates="games", link_model=PublisherGameLink
    )
    searches: list[Search] = Relationship(
        back_populates="games", link_model=GameSearchLink
    )
    # Self-referential relationships
    related_to: list["Game"] = Relationship(  # noqa:UP037
        link_model=RelatedGame,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==RelatedGame.source_game_id",
            "secondaryjoin": "Game.id==RelatedGame.target_game_id",
            "overlaps": "related_from",
        },
    )
    related_from: list["Game"] = Relationship(  # noqa:UP037
        link_model=RelatedGame,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==RelatedGame.target_game_id",
            "secondaryjoin": "Game.id==RelatedGame.source_game_id",
            "overlaps": "related_to",
        },
    )
    categories: list[Category] = Relationship(
        back_populates="games", link_model=GameCategoryLink
    )
    artists: list[Person] = Relationship(
        back_populates="games_illustrated",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==PersonGameLink.game_id",
            "secondaryjoin": "and_(Person.id==PersonGameLink.person_id, PersonGameLink.role_id==select(PersonRole.id).where(PersonRole.role=='artist').scalar_subquery())",
            "overlaps": "authors,games_authored",
        },
    )
    authors: list[Person] = Relationship(
        back_populates="games_authored",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==PersonGameLink.game_id",
            "secondaryjoin": "and_(Person.id==PersonGameLink.person_id, PersonGameLink.role_id==select(PersonRole.id).where(PersonRole.role=='author').scalar_subquery())",
            "overlaps": "artists,games_illustrated",
        },
    )
    collection_items: list[CollectionItem] = Relationship(
        back_populates="game"
    )


class UserSettings(SQLModel, table=True):
    id: bytes = BinaryUUIDField(primary_key=True, repr=False)
    keyword: str
    value: str


# Module-level engine creation
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)


def create_db_and_tables() -> None:
    """Creates database tables if they don't exist."""
    if DEBUG and os.path.exists(DB_FILE):
        # For debugging, start fresh each time.
        os.remove(DB_FILE)

        # Create tables after wiping
        SQLModel.metadata.create_all(engine)
    elif not DB_FILE.exists():
        # Create initial tables
        SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()

    with Session(engine) as session:  # Use the module-level engine
        # Add new roles and relationships first
        author_role = PersonRole(role="author")
        artist_role = PersonRole(role="artist")
        expansion_relationship = GameRelationship(type="expansion")

        session.add_all([author_role, artist_role, expansion_relationship])
        session.commit()

        session.refresh(author_role)
        session.refresh(artist_role)
        session.refresh(expansion_relationship)

        owned = OwnershipStatus(name="owned")
        category = Category(name="fun")
        publisher = Publisher(name="publisher")
        author = Person(name="author")
        artist = Person(name="artist")

        # Create game
        game = Game(
            bgg_id=13,  # Added bgg_id as it is now nullable=False
            name="Catan",
            version=3.0,
            image=b"img",
            description="desc",
            release_year=1996,
            min_players=2,
            max_players=3,
            recommended_players=3,
            min_age=10,
            min_play_time=10,
            max_play_time=20,
            bgg_rating=7.3,
            bgg_rank=105,
            complexity=2.1,
        )

        # Manually create links for publishers and categories
        publisher_link = PublisherGameLink(
            publisher_id=publisher.id, game_id=game.id
        )
        category_link = GameCategoryLink(
            category_id=category.id, game_id=game.id
        )

        # Manually create links for roles
        author_link = PersonGameLink(
            person_id=author.id, game_id=game.id, role_id=author_role.id
        )
        artist_link = PersonGameLink(
            person_id=artist.id, game_id=game.id, role_id=artist_role.id
        )

        # Create an expansion
        expansion = Game(
            bgg_id=362,  # Added bgg_id as it is now nullable=False
            name="Catan Expansion",
            version=3.0,
            image=b"img",
            description="desc",
            release_year=1996,
            min_players=5,
            max_players=6,
            min_age=10,
            min_play_time=60,
            max_play_time=90,
            complexity=2.1,
        )

        rel = RelatedGame(
            source_game_id=expansion.id,
            target_game_id=game.id,
            relationship_type_id=expansion_relationship.id,
        )

        collection = Collection(
            name="My Collection",
            username="user",
        )

        collection_item = CollectionItem(
            collection=collection, game=game, ownership_status=owned
        )

        session.add_all([
            owned,
            category,
            publisher,
            author,
            artist,
            game,
            expansion,
            publisher_link,
            category_link,
            author_link,
            artist_link,
            rel,
            collection,
            collection_item,
        ])
        session.commit()

        session.refresh(game)

        print("\n--- Output ---")
        print(f"Game: {game.name}")
        print(f"Expansions: {[g.name for g in game.related_from]}")
        print(f"Authors: {[p.name for p in game.authors]}")
        print(f"Artists: {[p.name for p in game.artists]}")
        print(f"Publishers: {[p.name for p in game.publishers]}")
        print(f"Categories: {[c.name for c in game.categories]}")
