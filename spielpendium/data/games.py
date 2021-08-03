from PyQt5 import QtCore
import pandas as pd


__all__ = ['Games']


class Games(QtCore.QAbstractTableModel):
    
    def __init__(self, parent=None):
        super(Games, self).__init__(parent)
        
        self._games = []
    
    def load(self, filename: str) -> bool:
        pass
    
    def save(self, filename: str) -> bool:
        pass
    

if __name__ == '__main__':
    games = Games()