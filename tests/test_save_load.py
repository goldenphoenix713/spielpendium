import unittest

from PyQt5 import QtCore, QtGui

from spielpendium.data import Games
from spielpendium.constants import IMAGE_SIZE

__author__ = 'Eduardo Ruiz'


class TestSaveLoad(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(TestSaveLoad, self).__init__(*args, **kwargs)
        test_im = (QtGui.QImage('../images/image.jpg')
                   .scaled(IMAGE_SIZE, IMAGE_SIZE, QtCore.Qt.KeepAspectRatio))

        self.data = [{
            'BGG Id': 1,
            'Image': test_im,
            'Name': 'Test',
            'Version': 1,
            'Author': 'Author',
            'Artist': 'Artist',
            'Publisher': 'Publisher Games',
            'Release Year': 2021,
            'Category': 'Made Up',
            'Description': 'This is a test thing I''m doing.',
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
        }]

        self.metadata = {
            'name': 'User'
        }

    def test_save(self):
        games = Games()
        games.append(self.data)

        for key, value in self.metadata.items():
            games.setData(key, value, QtCore.Qt.UserRole)

        self.assertTrue(games.save('test.splz'))

    def test_save_load(self):
        games1 = Games()
        games1.append(self.data)
        for key, value in self.metadata.items():
            games1.setData(key, value, QtCore.Qt.UserRole)

        games1.save('test.splz')

        games2 = Games()
        games2.load('test.splz')

        self.assertEqual(games1, games2)


if __name__ == '__main__':
    unittest.main()
