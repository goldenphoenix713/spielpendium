from datetime import datetime  # noqa: TC003
from uuid import UUID, uuid4  # noqa: TC003

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

# --- LINK MODELS ---


class GameSearchLink(SQLModel, table=True):
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    search_id: UUID = Field(
        foreign_key="search.id", primary_key=True, repr=False
    )


class RelatedGame(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    source_game_id: UUID = Field(foreign_key="game.id", repr=False)
    target_game_id: UUID = Field(foreign_key="game.id", repr=False)
    relationship_type: str


class GameCategoryLink(SQLModel, table=True):
    category_id: UUID = Field(
        foreign_key="category.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)


class PersonGameLink(SQLModel, table=True):
    person_id: UUID = Field(
        foreign_key="person.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    role: str = Field(primary_key=True)


class CollectionItem(SQLModel, table=True):
    collection_id: UUID = Field(
        foreign_key="collection.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    ownership_status_id: UUID = Field(
        foreign_key="ownershipstatus.id", repr=False
    )
    collection: "Collection" = Relationship(back_populates="items")  # noqa:UP037
    game: "Game" = Relationship(back_populates="collection_items")  # noqa:UP037
    ownership_status: "OwnershipStatus" = Relationship(  # noqa:UP037
        back_populates="collection_items"
    )


class PublisherGameLink(SQLModel, table=True):
    publisher_id: UUID = Field(
        foreign_key="publisher.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)


# --- MAIN MODELS ---


class Collection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    username: str
    name: str
    items: list[CollectionItem] = Relationship(back_populates="collection")


class Publisher(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="publishers", link_model=PublisherGameLink
    )


class Search(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    query: str
    date_time: datetime
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="searches", link_model=GameSearchLink
    )


class OwnershipStatus(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str
    collection_items: list[CollectionItem] = Relationship(
        back_populates="ownership_status"
    )


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str
    games_illustrated: list["Game"] = Relationship(  # noqa:UP037
        back_populates="artists",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Person.id==PersonGameLink.person_id",
            "secondaryjoin": "and_(Game.id==PersonGameLink.game_id, PersonGameLink.role=='artist')",
            "overlaps": "games_authored",
        },
    )
    games_authored: list["Game"] = Relationship(  # noqa:UP037
        back_populates="authors",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Person.id==PersonGameLink.person_id",
            "secondaryjoin": "and_(Game.id==PersonGameLink.game_id, PersonGameLink.role=='author')",
            "overlaps": "games_illustrated",
        },
    )


class Category(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str
    games: list["Game"] = Relationship(  # noqa:UP037
        back_populates="categories", link_model=GameCategoryLink
    )


class Game(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str
    sub_name: str | None = None
    version: float
    image: bytes = Field(repr=False)
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
    related_to: list["Game"] = Relationship(  # noqa:UP037
        link_model=RelatedGame,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==RelatedGame.source_game_id",
            "secondaryjoin": "Game.id==RelatedGame.target_game_id",
        },
    )
    related_from: list["Game"] = Relationship(  # noqa:UP037
        link_model=RelatedGame,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==RelatedGame.target_game_id",
            "secondaryjoin": "Game.id==RelatedGame.source_game_id",
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
            "secondaryjoin": "and_(Person.id==PersonGameLink.person_id, PersonGameLink.role=='artist')",
        },
    )
    authors: list[Person] = Relationship(
        back_populates="games_authored",
        link_model=PersonGameLink,
        sa_relationship_kwargs={
            "primaryjoin": "Game.id==PersonGameLink.game_id",
            "secondaryjoin": "and_(Person.id==PersonGameLink.person_id, PersonGameLink.role=='author')",
        },
    )
    collection_items: list[CollectionItem] = Relationship(
        back_populates="game"
    )


class UserSettings(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    keyword: str
    value: str


sqlite_file_name = "../../database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    import os

    if os.path.exists(sqlite_file_name):
        os.remove(sqlite_file_name)
    create_db_and_tables()
    with Session(engine) as session:
        owned = OwnershipStatus(name="owned")
        category = Category(name="fun")
        publisher = Publisher(name="publisher")
        author = Person(name="author")
        artist = Person(name="artist")
        game = Game(
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
            publishers=[publisher],
            categories=[category],
        )
        auth_link = PersonGameLink(
            person_id=author.id, game_id=game.id, role="author"
        )
        art_link = PersonGameLink(
            person_id=artist.id, game_id=game.id, role="artist"
        )
        expansion = Game(
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
            relationship_type="expansion",
        )
        collection = Collection(name="My Col", username="user")
        item = CollectionItem(
            collection=collection, game=game, ownership_status=owned
        )
        session.add_all([
            owned,
            category,
            publisher,
            author,
            artist,
            game,
            auth_link,
            art_link,
            expansion,
            rel,
            collection,
            item,
        ])
        session.commit()
        session.refresh(game)
        print(f"Game: {game.name}")
        print(f"Expansions: {[g.name for g in game.related_from]}")
        print(f"Authors: {[p.name for p in game.authors]}")
        print(f"Artists: {[p.name for p in game.artists]}")
