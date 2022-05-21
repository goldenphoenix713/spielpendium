"""Internal data storage for Spielpendium.

THe Games class is a QAbstractTableModel subclass that stores user
information when running Spielpendium. It contains methods that call the
save and load splz functions and allows data to be read in from the database.
"""

__all__ = ['Games']

from typing import Union, List, Any, Dict, Tuple

from PyQt5 import QtCore
import pandas as pd

try:
    from spielpendium.data.file_io import load_splz, save_splz
    from spielpendium.data.games_interface import import_user_data
except ModuleNotFoundError:
    from file_io import load_splz, save_splz
    from games_interface import import_user_data


class Games(QtCore.QAbstractTableModel):
    """The internal data storage class for Spielpendium."""
    _NUM_HIDDEN_COLS = 1
    _ID_COL = 0
    _IMAGE_COL = 1

    HEADER = [
        'BGG Id',
        'Image',
        'Name',
        'Version',
        'Author',
        'Artist',
        'Publisher',
        'Release Year',
        'Category',
        'Description',
        'Minimum Players',
        'Maximum Players',
        'Recommended Players',
        'Age',
        'Minimum Play Time',
        'Maximum Play Time',
        'BGG Rating',
        'BGG Rank',
        'Complexity',
        'Related Games',
    ]

    def __init__(self, parent: QtCore.QObject = None):
        """Initialize the Games object.

        :param parent: A parent QObject for Games.
        """
        super(Games, self).__init__(parent)

        self._games = pd.DataFrame(columns=self.HEADER)
        self._images = []
        self._metadata = {}

    def __repr__(self):
        """The representation of Games in the terminal."""
        return str(self)

    def __str__(self):
        """The string representation of Games."""
        return str(self._games)

    def __getitem__(self, index: Union[int, str, Tuple]) -> Any:
        """Enables indexing of Games.

        :param index: The index into Games
        :return: The item at the given index.
        :raises IndexError: If given an invalid index.
        """

        if isinstance(index, tuple):
            if len(index) == 1:
                index = index[0]
            elif len(index) == 2:
                if isinstance(index[0], int) and isinstance(index[1], int):
                    return self._games.iloc[index[0], index[1]]
                if isinstance(index[0], int) and isinstance(index[1], str):
                    return self._games[index[1]].iloc[index[0]]
                if isinstance(index[0], str) and isinstance(index[1], int):
                    return self._games.loc[index[0]].iloc[index[1]]
                if isinstance(index[0], str) and isinstance(index[1], str):
                    return self.games[index[1]].loc[index[0]]

                if isinstance(index[0], slice) \
                        and not isinstance(index[1], slice):
                    if isinstance(index[1], str):
                        return self._games[index[1]]
                    if isinstance(index[1], int):
                        return self._games.iloc[:, index[1]]
                elif not isinstance(index[0], slice) \
                        and isinstance(index[1], slice):
                    if isinstance(index[0], int):
                        return self._games.iloc[index[0]]
                elif isinstance(index[0], slice) \
                        and isinstance(index[1], slice):
                    return self._games

        if isinstance(index, str):
            return self._games[index]
        if isinstance(index, int):
            return self._games.iloc[index]

        raise IndexError('Indices must be a string, an integer, '
                         'a slice, or a 2-tuple.')

    def __eq__(self, other: 'Games') -> bool:
        """Checks for equality between two Games objects.

        :param other: Another Games instance.
        :return: True if the Games objects are equal, False otherwise.
        """

        # Make copies of the DataFrames
        copy_self: pd.DataFrame = self._games.copy()
        copy_other = other._games.copy()

        # Take the images out. These have to be checked separately
        image_col_self = copy_self.pop('Image')
        image_col_other = copy_other.pop('Image')

        # Check to make sure all elements are the same
        is_equal = True
        for row in range(len(copy_self)):
            for column in range(len(copy_self.columns)):
                if copy_self.iloc[row, column] != copy_other.iloc[row, column]:
                    is_equal = False
                    break

            # Check to see if the images are equal
            if is_equal:
                # Convert QImages to bytes
                # This makes a buffer in memory and saves the images as PNG
                # files into the memory buffer. Then it compares the raw bytes
                # of the PNG "file".
                self_ba = QtCore.QByteArray()
                self_buff = QtCore.QBuffer(self_ba)
                self_buff.open(QtCore.QIODevice.WriteOnly)
                image_col_self.iloc[row].save(self_buff, "PNG")
                self_im_bytes = self_buff.data()

                other_ba = QtCore.QByteArray()
                other_buff = QtCore.QBuffer(other_ba)
                other_buff.open(QtCore.QIODevice.WriteOnly)
                image_col_other.iloc[row].save(other_buff, "PNG")
                other_im_bytes = other_buff.data()

                # Check that the bytes equal
                is_equal = self_im_bytes == other_im_bytes

            if not is_equal:
                break

        # Check metadata equality
        if is_equal:
            is_equal = self._metadata == other._metadata

        return is_equal

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> int:
        """ Override method required by QAbstractTableModel subclasses.

        :param parent: A QModelIndex.
        :return: The number of rows in the model.
        """
        return len(self._games)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> int:
        """ Override method required by QAbstractTableModel subclasses.

        :param parent: A QModelIndex.
        :return: The number of columns in the model.
        """
        return len(self._games.columns) - self._NUM_HIDDEN_COLS

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation,
                   role: int = None) -> Union[List, QtCore.QVariant]:
        """ Override method required by QAbstractTableModel subclasses.

        :param section: The header column number.
        :param orientation: Horizontal or vertical
        :param role: A Qt role.
        :return: The header data.
        """
        # Only return the  header for a horizontal orientation
        # and a display role.
        if orientation != QtCore.Qt.Horizontal \
                or role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        return self.HEADER[section + self._NUM_HIDDEN_COLS]

    def flags(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> QtCore.Qt.ItemFlags:
        """ Override method required by QAbstractTableModel subclasses.
        Allows items to be editable.

        :param index: The index for the model item.
        :return: The Qt flags.
        """

        return super(Games, self).flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index: QtCore.QModelIndex, role=None) \
            -> Union[int, float, str, bytes, None]:
        """ Override method required by QAbstractTableModel subclasses.

        :param index: The index for the model item
        :param role: A Qt role.
        :return: The model data.
        """

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.DisplayRole \
                and column != self._IMAGE_COL - self._NUM_HIDDEN_COLS:
            return str(self._games.iloc[row, column + self._NUM_HIDDEN_COLS])
        if role == QtCore.Qt.ToolTipRole:
            return 'BGG ID: ' + str(self._games.iloc[row, self._ID_COL])
        if role == QtCore.Qt.DecorationRole \
                and column == self._IMAGE_COL - self._NUM_HIDDEN_COLS:
            return self._games.iloc[row, self._IMAGE_COL]
        return None

    def index(self, row: int, column: int,
              parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> QtCore.QModelIndex:
        """Creates an QModel index used by Qt to determine item locations in
        the model.

        :param row: The item row.
        :param column: The item column.
        :param parent: The parent of the index.
        :return: The QModelIndex for the given row and column.
        """

        return self.createIndex(row, column, self._games.iloc[
            row, column + self._NUM_HIDDEN_COLS])

    def insertRows(self, row: int, count: int,
                   parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """Insert new rows into the model and let connected views know.

        :param row: The first row to be inserted.
        :param count: The number of rows to be inserted.
        :param parent: A parent index.
        :return: True if the row insertion is successful, False otherwise.
        """

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            self._games.loc[len(self._games)] = [None] * self.columnCount()
        self.endInsertRows()

        return True

    def removeRows(self, row: int, count: int,
                   parent: QtCore.QModelIndex = None) -> bool:
        """Remove rows from the model.

        :param row: The starting row to remove.
        :param count: The number of rows to remove.
        :param parent: The parent index.
        :return: True if the row removal is successful, False otherwise.
        """
        self.beginRemoveRows(parent, row, row + count - 1)
        self._games.drop(range(row, row + count))
        self.endRemoveRows()

        return True

    def setData(self, index: Union[QtCore.QModelIndex, int, str], value: Any,
                role: int = None) -> bool:
        """Set data at a given index.

        :param index: The index in the model to insert data.
        :param value: The data to be inserted.
        :param role: THe Qt role of the data being inserted.
        :return: True if the data was successfully added, False otherwise.
        """
        if role == QtCore.Qt.EditRole:
            if index.isValid():
                self._games.iloc[index.row(),
                                 index.column() + self._NUM_HIDDEN_COLS] \
                    = str(value)
                self.dataChanged.emit(index, index,
                                      [QtCore.Qt.DisplayRole,
                                       QtCore.Qt.EditRole])
                return True
        elif QtCore.Qt.UserRole:
            if isinstance(index, (int, str)):
                self._metadata[index] = value
                return True
        return False

    def append(self, values: List) -> bool:
        """Add new data to the model. This method differs from setData in
        that this method adds an entire row at a time instead of one at a
        time.

        :param values: The information to add to the new row.
        :return: True if the appending is successful, False otherwise.
        """

        if not all([x in self.HEADER for x in values[0].keys()]):
            return False

        self.beginInsertRows(QtCore.QModelIndex(),
                             len(self._games),
                             len(self._games) + len(values) - 1)
        self._games = self._games.append(values, ignore_index=True)
        self.endInsertRows()
        return True

    def metadata(self) -> Dict:
        """Returns all the metadata of the Games object.

        :return:  The metadata of the Games object.
        """

        return self._metadata

    def load(self, filename: str) -> bool:
        """Loads data from a file into the Games object.

        :param filename: The path to the file to load.
        :return: True if the loading is successful, False otherwise.
        """
        try:
            new_games, new_metadata = load_splz(filename)
        except(FileNotFoundError, IOError):
            return False

        self.beginInsertRows(QtCore.QModelIndex(),
                             0, len(new_games) - 1)
        self._games = new_games[self.HEADER]
        self.endInsertRows()

        self._metadata = new_metadata

        return True

    def save(self, filename: str) -> bool:
        """Save the data in the Games object to a file.

        :param filename: The path to the save file.
        :return: True if the save is successful, False otherwise.
        """
        return save_splz(self._games, self._metadata, filename)

    def read_db(self) -> bool:
        """Reads information from the database.

        :return: True if the read is successful, False otherwise.
        """
        pass

    def write_db(self) -> bool:
        """Write information to the database.

        :return: True of the writing is successful, False otherwise.
        """
        pass

    def export(self, filename: str) -> bool:
        """Exports the information in the Games object to a pdf.

        :param filename: The path to the file to export.
        :return: True if the export is successful, False otherwise.
        """

        pass


if __name__ == '__main__':
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication([])

    test_data = import_user_data('phoenix713')

    view = QtWidgets.QTableView()
    header = view.verticalHeader()
    header.setDefaultSectionSize(64)
    header.sectionResizeMode(header.Fixed)
    games = Games()
    view.setModel(games)
    view.show()
    games.append(test_data)
    games.setData('name', 'Eduardo Ruiz', QtCore.Qt.UserRole)
    games.save('test.splz')
    games2 = Games()
    games2.load('test.splz')
    print(games2)
    print(games2['Image'])
    app.exec()
