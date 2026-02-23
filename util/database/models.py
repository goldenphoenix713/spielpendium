import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Publishers(Base):
    __tablename__ = "Publishers"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)


class Searches(Base):
    __tablename__ = "Searches"
    id = sa.Column(sa.Integer(), primary_key=True)
    query = sa.Column(sa.Text(), nullable=False, unique=True)
    date_time = sa.Column(sa.DateTime(), nullable=False)


class RecentFiles(Base):
    __tablename__ = "Recent_Files"
    id = sa.Column(sa.Integer(), primary_key=True)
    path = sa.Column(sa.Text(), nullable=False, unique=True)
    date_time = sa.Column(sa.DateTime(), nullable=False)


class GameRelationships(Base):
    __tablename__ = "Game_Relationships"
    id = sa.Column(sa.Integer(), primary_key=True)
    type = sa.Column(sa.Text(), nullable=False, unique=True)


class UserLists(Base):
    __tablename__ = "User_Lists"
    id = sa.Column(sa.Integer(), primary_key=True)
    username = sa.Column(sa.Text(), nullable=False, unique=True)
    xml = sa.Column(sa.Text(), nullable=False)
    last_refreshed = sa.Column(sa.DateTime(), nullable=False)


class OwnershipStatuses(Base):
    __tablename__ = "Ownership_Statuses"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)


class People(Base):
    __tablename__ = "People"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)


class Categories(Base):
    __tablename__ = "Categories"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)


class Games(Base):
    __tablename__ = "Games"
    id = sa.Column(sa.Integer(), primary_key=True, unique=True)
    timestamp = sa.Column(sa.DateTime(), nullable=False)
    name = sa.Column(sa.Text(), nullable=False)
    sub_name = sa.Column(sa.Text())
    version = sa.Column(sa.Integer(), nullable=False)
    image = sa.Column(sa.LargeBinary(), nullable=False)
    description = sa.Column(sa.Text(), nullable=False)
    publisher_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Publishers.id"), nullable=False
    )
    release_year = sa.Column(sa.Date(), nullable=False)
    min_players = sa.Column(sa.Integer(), nullable=False)
    max_players = sa.Column(sa.Integer(), nullable=False)
    recommended_players = sa.Column(sa.Integer())
    min_age = sa.Column(sa.Integer(), nullable=False)
    min_play_time = sa.Column(sa.Integer(), nullable=False)
    max_play_time = sa.Column(sa.Integer(), nullable=False)
    bgg_rating = sa.Column(sa.Float())
    bgg_rank = sa.Column(sa.Integer())
    complexity = sa.Column(sa.Float(), nullable=False)


class SearchResults(Base):
    __tablename__ = "Search_Results"
    game_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )
    search_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Searches.id"), primary_key=True
    )
    xml = sa.Column(sa.Text(), nullable=False)


class RelatedGames(Base):
    __tablename__ = "Related_Games"
    game1_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )
    game2_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )
    relationship_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Game_Relationships.id"), nullable=False
    )


class Authors(Base):
    __tablename__ = "Authors"
    id = sa.Column(sa.Integer(), primary_key=True)
    person_id = sa.Column(
        sa.Integer(), sa.ForeignKey("People.id"), nullable=False
    )


class UserListGames(Base):
    __tablename__ = "User_List_Games"
    id = sa.Column(sa.Integer(), primary_key=True)
    user__list_id = sa.Column(
        sa.Integer(), sa.ForeignKey("User_Lists.id"), nullable=False
    )
    game_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), nullable=False
    )
    ownership_status_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Ownership_Statuses.id"), nullable=False
    )


class GamesCategories(Base):
    __tablename__ = "Games_Categories"
    category_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Categories.id"), primary_key=True
    )
    game_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )


class Artists(Base):
    __tablename__ = "Artists"
    id = sa.Column(sa.Integer(), primary_key=True)
    person_id = sa.Column(
        sa.Integer(), sa.ForeignKey("People.id"), nullable=False
    )


class AuthorGame(Base):
    __tablename__ = "Author_Game"
    author_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Authors.id"), primary_key=True
    )
    game_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )


class ArtistGame(Base):
    __tablename__ = "Artist_Game"
    artist_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Artists.id"), primary_key=True
    )
    game_id = sa.Column(
        sa.Integer(), sa.ForeignKey("Games.id"), primary_key=True
    )


class UserSettings(Base):
    __tablename__ = "User_Settings"
    id = sa.Column(sa.Integer(), nullable=False)
    keyword = sa.Column(sa.Text(), nullable=False)
    value = sa.Column(sa.Text(), nullable=False)
