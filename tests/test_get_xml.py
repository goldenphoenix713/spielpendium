import unittest
from spielpendium.network import get_xml_info


class TestGetXml(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestGetXml, self).__init__(*args, **kwargs)
        self.url = 'https://www.boardgamegeek.com/xmlapi/boardgame/35424'

    def test_get_data(self):
        info = get_xml_info(self.url)
        self.assertEqual(type(info), type({}))


if __name__ == '__main__':
    unittest.main()
