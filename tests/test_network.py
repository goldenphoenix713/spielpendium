import unittest
from spielpendium.network import search_bgg, get_connection_status, \
    ConnectionStatus


class TestNetwork(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestNetwork, self).__init__(*args, **kwargs)
        self.search_term = 'Catan'

    def test_search(self):
        info = search_bgg(self.search_term)
        self.assertTrue(isinstance(info, dict))

    def test_connection_status(self):
        status = get_connection_status()
        self.assertTrue(isinstance(status, ConnectionStatus))


if __name__ == '__main__':
    unittest.main()
