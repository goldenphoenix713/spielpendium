import urllib.request
import urllib.error
import urllib.parse
from typing import Dict
import xml.parsers.expat
from json import dumps, loads

import xmltodict

from spielpendium.logger import set_log_level

__all__ = ['search_bgg']

_BOARD_GAME_GEEK_URL = 'https://www.boardgamegeek.com/xmlapi/'


@set_log_level('info')
def get_xml_info(url: str, **kwargs) -> Dict:
    """ Pulls xml info from the web and converts it to a dict.

    :param url: The URL that will be pulled to get XML data.
    :param kwargs: Additional parameters.

    :raises urllib.error.HTTPError: If there's any error in retrieving data at
            the URL.
    :raises ValueError: If the retrieved data cannot be converted to a dict

    :return: The information from the XML converted into a dict.
    """
    if 'logger' in kwargs.keys():
        logger = kwargs['logger']
    else:
        logger = None

    try:
        with urllib.request.urlopen(url) as file:
            data = file.read()
        if logger is not None:
            logger.debug(f'Data retrieved successfully from {url}.')
    except urllib.error.HTTPError as err:
        if logger is not None:
            logger.error(f'Data was unable to be retrieved from {url}. {err}')
        raise err from None

    # Convert the bytes object to a dict.
    # First, it gets converted to an OrderedDict
    # with xmltodict, and then to a dict via the
    # json library dumps and loads functions.
    try:
        data = loads(dumps(xmltodict.parse(data)))
        if logger is not None:
            logger.debug('Data successfully converted to dict.')
    except xml.parsers.expat.ExpatError:
        if logger is not None:
            logger.error(f'Data from {url} was unable to be read.')
        raise ValueError('Unable to read the information '
                         'at the provided URL.')from None
    if logger is not None:
        logger.info(f'Data successfully pulled from {url}.')

    return data


def search_bgg(search_query: str, exact_flag: bool = False, **kwargs) -> Dict:
    """ Assembles the search URL and returns data from the BoardGameGeek API.

    :param search_query: The query to search for.
    :param exact_flag: A flag that tells the BGG APT whether to only return
           exact matches or not.
    :return: Dictionary with the search results
    """
    exact_dict = {True: 1, False: 0}

    search_query = urllib.parse.quote(search_query)
    search_url = f'{_BOARD_GAME_GEEK_URL}search?search={search_query}' \
                 f'&exact={exact_dict[exact_flag]}'

    return get_xml_info(search_url, **kwargs)


if __name__ == '__main__':
    # test_url = 'https://www.boardgamegeek.com/xmlapi/boardgame/35424'
    # test_url = 'https://www.boardgamegeek.com/xmlapi2/boardgame/35424'
    # test_url = 'https://www.google.com'

    # info = get_xml_info(test_url)

    search_results = search_bgg('Catan')
    print(dumps(search_results, indent=2))

    # print(dumps(info, indent=2))
