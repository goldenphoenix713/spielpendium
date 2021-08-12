import unittest

from PyQt5 import QtCore, QtGui

from spielpendium.data import Games


class TestSaveLoad(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(TestSaveLoad, self).__init__(*args, **kwargs)
        test_im = (QtGui.QImage('../images/image.jpg')
                   .scaled(64, 64, QtCore.Qt.KeepAspectRatio))

        self.data = {
            'BGG Id': 1,
            'Image': test_im,
            'Name': 'Test',
            'Subname': 'The Test Thing',
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
        }

        self.metadata = {
            'name': 'User',
            'date': '2021-08-12',
        }

    def test_save_load(self):
        game1 = Games()
        game1.append(self.data)
        for key, value in self.metadata.items():
            game1.setData(key, value)

        game1.save('test.splz')

        game2 = Games()
        game2.load('test.splz')

        self.assertEqual(game1, game2)


if __name__ == '__main__':
    unittest.main()
