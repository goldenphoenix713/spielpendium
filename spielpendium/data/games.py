from PyQt5 import QtCore
import pandas as pd


__all__ = ['Games']


class Games(QtCore.QAbstractTableModel):
    
    def __init__(self, parent=None):
        super(Games, self).__init__(parent)
        
        # TODO Add more column names
        self._header = [
            'bgg_id',
            'game_name',
            'game_subname',
            'version',
            'author',
            'artist',
            'publisher',
            'release_year',
            'category',
            'image',
            'description',
            'min_players',
            'max_players',
            'recommended_players',
            'age',
            'min_play_time',
            'max_play_time',
            'bgg_rating',
            'bgg_rank',
            'complexity',
            'related_games',
        ]
        
        self._games = pd.DataFrame(columns=self._header)
    
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._games)
    
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._games.columns)
    
    def data(self, index, role):
        pass
    
    def index(self, row, column, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        return self.createIndex(row, column)
        
    
    def load(self, filename: str) -> bool:
        pass
    
    def save(self, filename: str) -> bool:
        pass
    
    def read_db(self) -> bool:
        pass
     
    def write_db(self) -> bool:
        pass
    

if __name__ == '__main__':
    games = Games()