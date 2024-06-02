import socket
import urllib.request
import urllib.error
import enum

from spielpendium.network import search_bgg

__author__ = 'Eduardo Ruiz'

__all__ = ['ConnectionStatus', 'get_connection_status']

_BGG_URL = "https://www.boardgamegeek.com/"
_HTTP_STATUS_OK = 200
_TEST_SEARCH_TERM = 'Catan'
_TEST_IP_ADDRESS = '1.1.1.1'
_TEST_PORT = 53


@enum.unique
class ConnectionStatus(enum.Enum):
    """ Enum class of connection statuses."""
    CONNECTION_OK = 0
    INTERNET_CONNECTION_DOWN = 1
    BOARDGAMEGEEK_DOWN = 2
    BOARDGAMEGEEK_API_DOWN = 3

    def __repr__(self):
        return self.name.title().replace('_', ' ')

    __str__ = __repr__


def is_connected_to_internet() -> bool:
    """Checks if there's an internet connection
    
    :return: True if an internet connection exists, False otherwise.
    """
    try:
        # try to connect to 1.1.1.1, a DNS server that should always be up
        connection = socket.create_connection((_TEST_IP_ADDRESS, _TEST_PORT))
        connection.close()
        return True
    except OSError:
        # if it can't connect, it'll come here
        pass
    return False


def bgg_is_up() -> bool:
    """Checks if boardgamegeek.com is up

    :return: True if boardgamegeek.com is up, False otherwise.
    """

    try:
        # try to connect to.BGG and check the return status.
        return urllib.request.urlopen(_BGG_URL).getcode() == _HTTP_STATUS_OK
    except urllib.error.URLError:
        # if there's any error with connecting, return False
        pass

    return False


def bgg_api_is_up() -> bool:
    """

    :return: True if the BGG API is working, False otherwise
    """

    try:
        # Try a test search using the BGG API. It is works, the API is up
        search_bgg(_TEST_SEARCH_TERM)
        return True
    except urllib.error.HTTPError:
        # If it doesn't work, the API is down
        pass

    return False


def get_connection_status() -> ConnectionStatus:
    """ Checks that there's an internet connection and connections to BGG.

    :return: The connection status.
    """

    if not is_connected_to_internet():
        # First check the internet connection.
        return ConnectionStatus.INTERNET_CONNECTION_DOWN
    elif not bgg_is_up():
        # Then check the status of BBG website.
        return ConnectionStatus.BOARDGAMEGEEK_DOWN
    elif not bgg_api_is_up():
        # Then check the status of the BGG API.
        return ConnectionStatus.BOARDGAMEGEEK_API_DOWN
    else:
        # If all previous were good, return a good status.
        return ConnectionStatus.CONNECTION_OK


if __name__ == '__main__':
    print(get_connection_status())
