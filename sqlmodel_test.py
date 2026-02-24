from datetime import date, datetime  # noqa: TC003
from uuid import UUID, uuid4  # noqa: TC003

from sqlmodel import Field, Relationship, SQLModel


class Publisher(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str

    game: str = Relationship(back_populates="publisher")


class Search(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    query: str
    date_time: datetime


class RecentFile(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    path: str
    date_time: datetime


class GameRelationship(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: str


class UserList(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str
    xml: str
    last_refreshed: datetime


class OwnershipStatus(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str


class Category(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str


class Game(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime
    name: str
    sub_name: str | None
    version: int
    image: bytes
    description: str
    publisher_id: UUID = Field(foreign_key="Publisher.id")
    release_year: date
    min_players: int
    max_players: int
    recommended_players: int | None
    min_age: int
    min_play_time: int
    max_play_time: int
    bgg_rating: float | None
    bgg_rank: int | None
    complexity: float

    publisher: str = Relationship(back_populates="game")


class SearchResults(SQLModel, table=True):
    game_id: UUID = Field(foreign_key="Game.id", primary_key=True)
    search_id: UUID = Field(foreign_key="Search.id", primary_key=True)
    xml: str


class RelatedGame(SQLModel, table=True):
    game1_id: UUID = Field(foreign_key="Game.id", primary_key=True)
    game2_id: UUID = Field(foreign_key="Game.id", primary_key=True)
    relationship_id: UUID = Field(
        foreign_key="GameRelationship.id", primary_key=True
    )


class Author(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    person_id: UUID = Field(foreign_key="Person.id")


class UserListGame(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_list_id: UUID = Field(foreign_key="UserList.id")
    game_id: UUID = Field(foreign_key="Game.id")
    ownership_status_id: UUID = Field(foreign_key="OwnershipStatus.id")


class GamesCategory(SQLModel, table=True):
    category_id: UUID = Field(foreign_key="Category.id", primary_key=True)
    game_id: UUID = Field(foreign_key="Game.id", primary_key=True)


class Artist(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    person_id: UUID = Field(foreign_key="Person.id")


class AuthorGame(SQLModel, table=True):
    author_id: UUID = Field(foreign_key="Author.id", primary_key=True)
    game_id: UUID = Field(foreign_key="Game.id", primary_key=True)


class ArtistGame(SQLModel, table=True):
    artist_id: UUID = Field(foreign_key="Artist.id", primary_key=True)
    game_id: UUID = Field(foreign_key="Game.id", primary_key=True)


class UserSettings(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    keyword: str
    value: str
