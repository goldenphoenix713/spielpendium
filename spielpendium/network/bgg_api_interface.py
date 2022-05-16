"""The BGG API side of the Spielpendium-BGG interface."""
import time
import urllib.request
import urllib.error
import urllib.parse
import multiprocessing as mp
from typing import Dict, Optional, List, Union

from PyQt5 import QtGui, QtCore
import xmltodict

from spielpendium import log

__all__ = ['search_bgg', 'get_user_game_collection', 'get_game_info',
           'get_images']

_BGG_API_URL = 'https://www.boardgamegeek.com/xmlapi/'

# noinspection SpellCheckingInspection
COLLECTION_FILTERS = (
    'own',
    'rated',
    'played',
    'comment',
    'trade',
    'want',
    'wantintrade',
    'wishlist',
    'wanttoplay',
    'wanttobuy',
    'prevowned',
    'preordered',
    'hasparts',
    'wantparts',
    'notifycontent',
    'notifysale',
    'notifyaution',
    'wishlistpriority',
    'minrating',
    'maxrating',
    'minbggrating',
    'maxbggrating',
    'minplays',
    'maxplays',
    'showprivate',
)


@log.log(log.logger)
def get_xml_info(url: str) -> dict:
    """ Pulls xml info from the web and converts it to a dict.

    :param url: The URL that will be pulled to get XML data.
    :raises urllib.error.HTTPError: If there's any error in retrieving data at
            the URL.
    :raises ValueError: If the retrieved data cannot be converted to a dict
    :return: The information from the XML converted into a dict.
    """
    first_loop = True

    while True:
        with urllib.request.urlopen(url) as webpage:
            data_bytes = webpage.read()
        log.logger.debug(f'Information retrieved successfully from {url}.')

        # Convert the bytes object to an OrderedDict.
        data = xmltodict.parse(data_bytes)
        log.logger.debug('Data successfully converted to dict.')
        # except xml.parsers.expat.ExpatError:
        #     if logger is not None:
        #         logger.error(f'Data from {url} was unable to be read.')
        #     raise ValueError('Unable to read the information '
        #                      'at the provided URL.') from None

        if 'message' not in data.keys():
            log.logger.info(f'Data successfully pulled from {url}.')
            break
        else:
            if first_loop:
                log.logger.info(f'Waiting for API to generate data at {url}.')
                first_loop = False
            else:
                log.logger.info(f'Still waiting for API to generate data.')
            time.sleep(10)

    return data


def search_bgg(search_query: str, exact_flag: bool = False) -> dict:
    """ Assembles the search URL and returns data from the BoardGameGeek API.

    :param search_query: The query to search for.
    :param exact_flag: A flag that tells the BGG APT whether to only return
           exact matches or not.
    :return: Dictionary with the search results
    """
    search_query = urllib.parse.quote(search_query)
    search_url = (f'{_BGG_API_URL}search?search={search_query}'
                  f'&exact={int(exact_flag)}')

    return get_xml_info(search_url)


def get_user_game_collection(
        username: str,
        filters: Optional[Dict[str, Union[int, bool]]] = None
) -> dict:
    """ Grabs a user's game collection from BGG.

    :param username: The username whose collection were grabbing.
    :param filters: Additional filters for the game collection.
    :return: A dictionary with the user's game collection.
    """
    username_safe = urllib.parse.quote(username)
    collection_url = f'{_BGG_API_URL}collection/{username_safe}'

    if filters is not None:
        if any([key not in COLLECTION_FILTERS for key in filters.keys()]):
            raise KeyError('Invalid filter provided. Filters must be '
                           'one of the following: "' +
                           '", "'.join(list(COLLECTION_FILTERS)) + '".')

        collection_url += '?' + '&'.join(
            [f'{key}={int(value)}' for key, value in filters.items()]
        )

    return get_xml_info(collection_url)


def get_game_info(game_ids: Union[int, List[int]],
                  get_stats: bool = False) -> dict:
    """ Gets details for a game with a certain game id.

    :param game_ids: The BGG game id(s) to get information for.
    :param get_stats: Whether to get detailed game stats or not.
    :return: The details of the game(s).
    """

    if isinstance(game_ids, int):
        game_ids = [game_ids]

    url = _BGG_API_URL + 'boardgame/' + ','.join([str(a) for a in game_ids])

    if get_stats:
        url = url + f'?stats=1'

    return get_xml_info(url)


def get_images(image_urls: Union[str, List[str]]) -> List[QtGui.QImage]:
    """ Retrieves images from a list of URLs.

    :param image_urls: The image URLs.
    :return: The images.
    """
    if isinstance(image_urls, str):
        image_urls = [image_urls]

    pool = mp.Pool(processes=mp.cpu_count())
    images_as_bytes = pool.map(get_single_image, image_urls)
    images_qt = [QtGui.QImage.fromData(im).scaled(
        256, 256, QtCore.Qt.KeepAspectRatio
    ) for im in images_as_bytes]

    return images_qt


def get_single_image(image_url: str) -> bytes:
    """ Gets the image at the requested url.

    :param image_url: The image url.
    :return: The image as bytes.
    """

    with urllib.request.urlopen(image_url) as url:
        image = url.read()

    return image


if __name__ == '__main__':
    from json import dumps

    test_url = 'https://www.boardgamegeek.com/xmlapi/boardgame/35424'
    info = get_xml_info(test_url)
    print(dumps(info, indent=2))

    search_results = search_bgg('Catan')
    print(dumps(search_results, indent=2))

    collection = get_user_game_collection('phoenix713', filters={'own': True})
    print(dumps(collection, indent=2))

    game_details = get_game_info([224125, 255907])
    print(dumps(game_details, indent=2))

    test_image = ('https://cf.geekdo-images.com/vpET5JF4hXUXA6bqXx0WlQ__'
                  'original/img/FyZogAqdllhWqFns_zfjhaUP6jM=/0x0/filters:'
                  'format(jpeg)/pic4854460.jpg')
    images = get_images(test_image)
    print(images)
    images[0].save('test.png', 'png')
