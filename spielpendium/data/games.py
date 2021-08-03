from PyQt5 import QtCore
import pandas as pd


__all__ = ['Games']


class Games(QtCore.QAbstractTableModel):
    
    def __init__(self, parent=None):
        super(Games, self).__init__(parent)
        
        # TODO Add more column names
        column_names = [
            'bgg_id',
            'game_name',
            'game_subname',
            'author',
            'artist',
            'publisher',
            'category',
            'image',
            'description',
            'min_players',
            'max_players',
            'recommended_players',
            'age',
            'complexity',
        ]
        
        self._games = pd.DataFrame(columns=column_names)
    
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