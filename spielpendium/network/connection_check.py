import socket
import urllib.request
import urllib.error
import enum

from spielpendium.network import search_bgg

__all__ = ['ConnectionStatus', 'get_connection_status']

_BGG_URL = "https://www.boardgamegeek.com/"


@enum.unique
class ConnectionStatus(enum.Enum):
    """ Enum class of connection statuses."""
    CONNECTION_OK = enum.auto()
    INTERNET_CONNECTION_DOWN = enum.auto()
    BOARDGAMEGEEK_DOWN = enum.auto()
    BOARDGAMEGEEK_API_DOWN = enum.auto()

    def __repr__(self):
        return self.name.title().replace('_', ' ')

    def __str__(self):
        return repr(self)


def is_connected_to_internet() -> bool:
    """Checks if there's an internet connection
    
    :return: True if an internet connection exists, False otherwise.
    """
    try:
        # try to connect to 1.1.1.1, a DNS server that should always be up
        socket.create_connection(("1.1.1.1", 53))
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
        # 200 means "ok success status"
        return urllib.request.urlopen(_BGG_URL).getcode() == 200
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
        search_bgg('Catan', logger=None)
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
