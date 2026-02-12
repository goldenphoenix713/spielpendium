import enum
import urllib.error

import requests

from api import search_bgg

__author__ = "Eduardo Ruiz"

__all__ = ["ConnectionStatus", "get_connection_status"]

_TEST_SEARCH_TERM = "Catan"


@enum.unique
class ConnectionStatus(enum.Enum):
    """Enum class of connection statuses."""

    CONNECTION_OK = 0
    BOARDGAMEGEEK_DOWN = 1
    BOARDGAMEGEEK_API_DOWN = 2

    def __repr__(self) -> str:
        return self.name.title().replace("_", " ")

    __str__ = __repr__


def bgg_is_up() -> bool:
    """Checks if boardgamegeek.com is up

    :return: True if boardgamegeek.com is up, False otherwise.
    """

    # try to connect to BGG and check the return status.
    try:
        response = requests.head("https://www.boardgamegeek.com/")
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
    ):
        return False
    return True


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
    """Checks that there's an internet connection and connections to BGG.

    :return: The connection status.
    """

    if not bgg_is_up():
        # Then check the status of BBG website.
        return ConnectionStatus.BOARDGAMEGEEK_DOWN
    elif not bgg_api_is_up():
        # Then check the status of the BGG API.
        return ConnectionStatus.BOARDGAMEGEEK_API_DOWN
    else:
        # If all previous were good, return a good status.
        return ConnectionStatus.CONNECTION_OK


if __name__ == "__main__":
    print(get_connection_status())
