from typing import Union, List, Any, Dict

from PyQt5 import QtCore
import pandas as pd

from spielpendium.data.file_io import *

__all__ = ['Games']


class Games(QtCore.QAbstractTableModel):
    _NUM_HIDDEN_COLS = 2
    _ID_COL = 0
    _IMAGE_COL = 1

    def __init__(self, parent: QtCore.QObject = None):
        super(Games, self).__init__(parent)

        self._header = [
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

        self._games = pd.DataFrame(columns=self._header)

    def __repr__(self):
        return self._games

    def __str__(self):
        return str(self._games)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> int:
        return len(self._games)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> int:
        return len(self._games.columns) - self._NUM_HIDDEN_COLS

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation,
                   role: int = None) -> Union[List, QtCore.QVariant]:

        if orientation != QtCore.Qt.Horizontal \
                or role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        return self._header[section + self._NUM_HIDDEN_COLS]

    def flags(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) \
            -> QtCore.Qt.ItemFlags:

        return super(Games, self).flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index: QtCore.QModelIndex, role=None) \
            -> Union[int, float, str, bytes]:

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

        return self.createIndex(row, column, self._games.iloc[row, column])

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

    def setData(self, index: QtCore.QModelIndex, value: Any,
                role: int = None) -> bool:
        if index.isValid() and role == QtCore.Qt.EditRole:
            self._games.iloc[index.row(),
                             index.column() + self._NUM_HIDDEN_COLS] \
                = str(value)
            self.dataChanged.emit(index, index,
                                  [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
            return True
        return False

    def append(self, values: Dict) -> bool:
        try:
            if not all([x in self._header for x in values.keys()]):
                raise KeyError
            self.beginInsertRows(QtCore.QModelIndex(),
                                 len(self._games), len(self._games))
            self._games = self._games.append(values, ignore_index=True)
            self.endInsertRows()
        except KeyError:
            return False

    def load(self, filename: str) -> bool:
        new_games = load_spl(filename)

        self.beginInsertRows(QtCore.QModelIndex(),
                             1, len(new_games)-1)
        self._games = new_games
        self.endInsertRows()

        return True

    def save(self, filename: str) -> bool:
        try:
            save_spl(self._games, filename)
            return True
        except FileNotFoundError:
            return False

        # TODO Add more exception types

    def read_db(self) -> bool:
        pass

    def write_db(self) -> bool:
        pass


if __name__ == '__main__':
    from PyQt5 import QtWidgets

    data = {
        'BGG Id': 1,
        'Image': 'image',
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

    app = QtWidgets.QApplication([])
    view = QtWidgets.QTableView()
    games = Games()
    print(games)
    print(games.rowCount())
    print(games.columnCount())
    view.setModel(games)
    view.show()
    games.append(data)
    print(games)
    games.save('test')
    app.exec()
