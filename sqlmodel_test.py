from datetime import datetime  # noqa: TC003
from uuid import UUID, uuid4  # noqa: TC003

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine


#
class GameSearchLink(SQLModel, table=True):
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    search_id: UUID = Field(
        foreign_key="search.id", primary_key=True, repr=False
    )
    # xml: str


class RelatedGame(SQLModel, table=True):
    game1_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    game2_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    relationship_id: UUID = Field(
        foreign_key="gamerelationship.id", primary_key=True
    )


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


class CollectionItem(SQLModel, table=True):
    collection_id: UUID = Field(
        foreign_key="collection.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)
    ownership_status_id: UUID = Field(
        foreign_key="ownershipstatus.id", repr=False
    )

    collection: "Collection" = Relationship(back_populates="items")  # noqa: UP037
    game: "Game" = Relationship(back_populates="collection_items")  # noqa: UP037
    ownership_status: "OwnershipStatus" = Relationship(  # noqa: UP037
        back_populates="collection_items"
    )

    def __repr__(self):
        return (
            f"CollectionItem(collection=Collection({self.collection}), "
            f"game=Game({self.game}), ownership_status"
            f"={self.ownership_status})"
        )


class PublisherGameLink(SQLModel, table=True):
    publisher_id: UUID = Field(
        foreign_key="publisher.id", primary_key=True, repr=False
    )
    game_id: UUID = Field(foreign_key="game.id", primary_key=True, repr=False)


class Collection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    username: str

    items: list[CollectionItem] = Relationship(back_populates="collection")

    def __repr__(self):
        return (
            f"Collection(username={self.username}, games="
            f"{[x.game for x in self.items]})"
        )


class Publisher(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str

    games: list["Game"] = Relationship(  # noqa: UP037
        back_populates="publishers", link_model=PublisherGameLink
    )


class Search(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    query: str
    date_time: datetime

    games: list["Game"] = Relationship(  # noqa: UP037
        back_populates="searches", link_model=GameSearchLink
    )


class GameRelationship(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    type: str


class OwnershipStatus(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str

    collection_items: list[CollectionItem] = Relationship(
        back_populates="ownership_status"
    )


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str

    games_illustrated: list["Game"] = Relationship(  # noqa: UP037
        back_populates="artists", link_model=PersonGameLink
    )
    games_authored: list["Game"] = Relationship(  # noqa: UP037
        back_populates="authors",
        link_model=PersonGameLink,
    )


class Category(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    name: str

    games: list["Game"] = Relationship(  # noqa: UP037
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
    # related_games: list[Game] = Relationship(
    #     back_populates="related_games", link_model=RelatedGame
    # )
    categories: list[Category] = Relationship(
        back_populates="games", link_model=GameCategoryLink
    )
    artists: list[Person] = Relationship(
        back_populates="games_illustrated", link_model=PersonGameLink
    )
    authors: list[Person] = Relationship(
        back_populates="games_authored", link_model=PersonGameLink
    )
    collection_items: list[CollectionItem] = Relationship(
        back_populates="game"
    )


class UserSettings(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, repr=False)
    keyword: str
    value: str


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()

    with Session(engine) as session:
        owned = OwnershipStatus(name="owned")
        category = Category(name="fun")
        publisher = Publisher(name="publisher")
        author = Person(name="author")
        artist = Person(name="artist")

        game = Game(
            name="Catan",
            version=3,
            image=b"image",
            description="description",
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
            authors=[author],
            artists=[artist],
        )

        collection = Collection(
            name="collection",
            username="phoenix713",
            games=[game],
        )

        collection_item = CollectionItem(
            collection=collection, game=game, ownership_status=owned
        )

        session.add(collection_item)
        session.commit()

        session.refresh(collection_item)
        session.refresh(collection)
        session.refresh(game)
