"""Internal data storage for Spielpendium.

THe Games class is a QAbstractTableModel subclass that stores user
information when running Spielpendium. It contains methods that call the
save and load splz functions and allows data to be read in from the database.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

# from data.games_interface import import_user_data

__author__ = "Eduardo Ruiz"

__all__ = ["Games"]


@dataclass(frozen=True)
class Game:
    """The internal data storage class for Spielpendium games."""

    bgg_id: int
    image: bytearray
    name: str
    version: str
    author: str
    artist: str
    publisher: str
    release_year: int
    category: str
    description: str
    minimum_players: int
    maximum_players: int
    recommended_players: int
    age: int
    minimum_play_time: int
    maximum_play_time: int
    bgg_rating: float
    bgg_rank: int
    complexity: float
    related_games: tuple[str]

    def to_series(self) -> pd.Series:
        return pd.Series(asdict(self))

    # @classmethoduv
    # def from_bgg(cls, name: str) -> Game:
    #     pass


class Games(list):  # type: ignore[type-arg]
    """The internal data storage class for Spielpendium games."""

    def __init__(self, *args: tuple[Game, ...]) -> None:
        """Initialize the Games object."""

        if not all(isinstance(arg, Game) for arg in args):
            raise TypeError("Inputs must all be Game instances.")

        super().__init__(*args)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(x) for x in self])

    @property
    def header(self) -> tuple[str, ...]:
        return tuple(Game.__dataclass_fields__.keys())


if __name__ == "__main__":
    pass

#
# class Games:
#     """The internal data storage class for Spielpendium."""
#
#     HEADER = [
#         "BGG Id",
#         "Image",
#         "Name",
#         "Version",
#         "Author",
#         "Artist",
#         "Publisher",
#         "Release Year",
#         "Category",
#         "Description",
#         "Minimum Players",
#         "Maximum Players",
#         "Recommended Players",
#         "Age",
#         "Minimum Play Time",
#         "Maximum Play Time",
#         "BGG Rating",
#         "BGG Rank",
#         "Complexity",
#         "Related Games",
#     ]
#
#     def __init__(self):
#         """Initialize the Games object."""
#
#         self._games: pd.DataFrame = pd.DataFrame(columns=self.HEADER)
#
#     def __repr__(self):
#         """The representation of Games in the terminal."""
#         return str(self)
#
#     def __str__(self):
#         """The string representation of Games."""
#         return str(self._games)
#
#     def __getitem__(
#         self,
#         index: (
#             int
#             | str
#             | tuple[int | str]
#             | tuple[int | str | slice, int | str | slice]
#         ),
#     ) -> Any:
#         """Enables indexing of Games.
#
#         :param index: The index into Games
#         :return: The item at the given index.
#         :raises IndexError: If given an invalid index.
#         """
#
#         if isinstance(index, tuple):
#             if len(index) == 1:
#                 index = index[0]
#             elif len(index) == 2:
#                 if isinstance(index[0], int) and isinstance(index[1], int):
#                     return self._games.iloc[index[0], index[1]]
#                 if isinstance(index[0], int) and isinstance(index[1], str):
#                     return self._games[index[1]].iloc[index[0]]
#                 if isinstance(index[0], str) and isinstance(index[1], int):
#                     return self._games.loc[index[0]].iloc[index[1]]
#                 if isinstance(index[0], str) and isinstance(index[1], str):
#                     return self._games[index[1]].loc[index[0]]
#
#                 if isinstance(index[0], slice) and not isinstance(
#                     index[1], slice
#                 ):
#                     if isinstance(index[1], str):
#                         return self._games[index[1]]
#                     if isinstance(index[1], int):
#                         return self._games.iloc[:, index[1]]
#                 elif not isinstance(index[0], slice) and isinstance(
#                     index[1], slice
#                 ):
#                     if isinstance(index[0], int):
#                         return self._games.iloc[index[0]]
#                 elif isinstance(index[0], slice) and isinstance(
#                     index[1], slice
#                 ):
#                     return self._games
#
#         if isinstance(index, str):
#             return self._games[index]
#         if isinstance(index, int):
#             return self._games.iloc[index]
#
#         raise IndexError(
#             "Indices must be a string, an integer, a slice, or a 2-tuple."
#         )
#
#     def __eq__(  # pyright:ignore[reportIncompatibleMethodOverride]
#         self, other: object
#     ) -> bool:
#         """Checks for equality between two Games objects.
#
#         :param other: Another Games instance.
#         :return: True if the Games objects are equal, False otherwise.
#         """
#         if not isinstance(other, Games):
#             return NotImplemented
#
#         # Make copies of the DataFrames
#         copy_self: pd.DataFrame = self._games.copy()
#         copy_other = other._games.copy()
#
#         # Check to make sure all elements are the same
#         is_equal = copy_self.equals(copy_other)
#
#         # Check metadata equality
#         if is_equal:
#             is_equal = self._games.attrs == other._games.attrs
#
#         return is_equal
#
#     def append(self, values: list[dict[str, str]]):
#         """Add new data to the games data
#
#         :param values: The information to add to the new row.
#         :return: True if the appending is successful, False otherwise.
#         """
#
#         if not all(x in self.HEADER for x in values[0]):
#             return
#
#         values_df = pd.DataFrame(values)
#
#         self._games = pd.concat([self._games, values_df], ignore_index=True)
#
#     @property
#     def metadata(self) -> dict[str, str]:
#         """Returns all the metadata of the Games object.
#
#         :return:  The metadata of the Games object.
#         """
#
#         return self._games.attrs
#
#     # def load(self, filename: str) -> bool:
#     #     """Loads data from a file into the Games object.
#     #
#     #     :param filename: The path to the file to load.
#     #     :return: True if the loading is successful, False otherwise.
#     #     """
#     #     try:
#     #         new_games, new_metadata = load_splz(filename)
#     #     except (OSError, FileNotFoundError):
#     #         return False
#     #
#     #     self._games = new_games[self.HEADER]
#     #
#     #     self._games.attrs = new_metadata
#     #
#     #     return True
#
#     # def save(self, filename: str) -> bool:
#     #     """Save the data in the Games object to a file.
#     #
#     #     :param filename: The path to the save file.
#     #     :return: True if the save is successful, False otherwise.
#     #     """
#     #     return save_splz(self._games, self._games.attrs, filename)
#
#     def read_db(self):
#         """Reads information from the database."""
#         pass
#
#     def write_db(self):
#         """Write information to the database."""
#         pass
#
#     def export(self, filename: str):
#         """Exports the information in the Games object to a pdf.
#
#         :param filename: The path to the file to export.
#         """
#
#         pass


# if __name__ == "__main__":
#     test_data = import_user_data("phoenix713")
#
#     games = Games()
#     games.append(test_data)
#     print(games)
