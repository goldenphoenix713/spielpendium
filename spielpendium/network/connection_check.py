import socket
import urllib.request
import urllib.error

from spielpendium.network import search_bgg

__all__ = ['is_connected_to_internet', 'bgg_is_up', 'bgg_api_is_up']

_BGG_URL = "https://www.boardgamegeek.com/"


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


if __name__ == '__main__':
    print(is_connected_to_internet())
    print(bgg_is_up())
    print(bgg_api_is_up())
