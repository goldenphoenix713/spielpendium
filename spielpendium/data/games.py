"""Internal data storage for Spielpendium.

THe Games class is a QAbstractTableModel subclass that stores user
information when running Spielpendium. It contains methods that call the
save and load splz functions and allows data to be read in from the database.
"""

__all__ = ['Games']

from typing import Union, List, Any, Dict

from PyQt5 import QtCore, QtGui
import pandas as pd

try:
    from spielpendium.data.file_io import load_splz, save_splz
except ModuleNotFoundError:
    from file_io import load_splz, save_splz

class Games(QtCore.QAbstractTableModel):
    """The internal data storage class for Spielpendium."""
    _NUM_HIDDEN_COLS = 2
    _ID_COL = 0
    _IMAGE_COL = 1

    HEADER = [
        'BGG Id',
        'Image',
        'Name',
        'Subname',
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
        return self._games

    def __str__(self):
        return str(self._games)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> int:
        """ Override method required by QAbstractTableModel subclasses.

        :param parent: A QModelIndex.
        :return: THe number of rows in the model.
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
            -> Union[int, float, str, bytes]:
        """ Override method required by QAbstractTableModel subclasses.

        :param index: The index for the model item
        :param role: A Qt role.
        :return: The model data.
        """

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            return str(self._games.iloc[row, column + self._NUM_HIDDEN_COLS])
        elif role == QtCore.Qt.ToolTipRole:
            return 'BGG ID: ' + str(self._games.iloc[row, self._ID_COL])
        elif role == QtCore.Qt.DecorationRole and column == 0:
            return self._games.iloc[row, self._IMAGE_COL]

    def index(self, row: int, column: int,
              parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> QtCore.QModelIndex:
        return self.createIndex(row, column, self._games.iloc[row, column + self._NUM_HIDDEN_COLS])

    def insertRows(self, row: int, count: int,
                   parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:

        self.beginInsertRows(parent, row, row + count - 1)
        for ii in range(count):
            self._games.loc[len(self._games)] = [None] * self.columnCount()
        self.endInsertRows()

        return True

    def removeRows(self, row: int, count: int,
                   parent: QtCore.QModelIndex = None) -> bool:
        self.beginRemoveRows(parent, row, row + count - 1)
        self._games.drop(range(row, row + count))
        self.endRemoveRows()

        return True

    def setData(self, index: Union[QtCore.QModelIndex, int, str], value: Any,
                role: int = None) -> bool:
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

    def append(self, values: Dict) -> bool:
        if not all([x in self.HEADER for x in values.keys()]):
            return False
        
        self.beginInsertRows(QtCore.QModelIndex(),
                                 len(self._games), len(self._games))
        self._games = self._games.append(values, ignore_index=True)
        self.endInsertRows()
        return True

    def load(self, filename: str) -> bool:
        try:
            new_games, new_metadata = load_splz(filename)
        except(FileNotFoundError, TypeError):
            return False

        self.beginInsertRows(QtCore.QModelIndex(),
                             0, len(new_games)-1)
        self._games = new_games
        self.endInsertRows()

        self._metadata = new_metadata

        return True

    def save(self, filename: str) -> bool:
        return save_splz(self._games, self._metadata, filename)

    def read_db(self) -> bool:
        pass

    def write_db(self) -> bool:
        pass


if __name__ == '__main__':
    from PyQt5 import QtWidgets
    from PIL import Image
    
    app = QtWidgets.QApplication([])
    
    test_im = QtGui.QImage('../../images/image.jpg')

    test_data = {
        'BGG Id': 1,
        'Image': test_im,
        'Name': 'Test',
        'Subname': 'The Test Thing',
        'Version': 1,
        'Author': 'Eddie',
        'Artist': 'Eddie',
        'Publisher': 'Eddie Games',
        'Release Year': 2021,
        'Category': 'Made Up',
        'Description': 'This is a test thingy I''m doing.',
        'Minimum Players': 3,
        'Maximum Players': 5,
        'Recommended Players': 4,
        'Age': 20,
        'Minimum Play Time': 50,
        'Maximum Play Time': 120,
        'BGG Rating': 1.2,
        'BGG Rank': 504033,
        'Complexity': 1.2,
        'Related Games': 'None',
    }
    
    view = QtWidgets.QTableView()
    games = Games()
    print(games)
    print(games.rowCount())
    print(games.columnCount())
    view.setModel(games)
    view.show()
    games.append(test_data)
    print(games.rowCount())
    print(games.columnCount())
    games.setData('name', 'Eduardo Ruiz', QtCore.Qt.UserRole)
    print(games)
    games.save('test.splz')
    games.load('test.splz')
    print(games)
    print(games._games['Image'])
    app.exec()
