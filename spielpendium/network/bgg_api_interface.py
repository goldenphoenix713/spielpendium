"""The BGG API side of the Spielpendium-BGG interface."""
import time
import urllib.request
import urllib.error
import urllib.parse
import multiprocessing as mp
from typing import Dict, Optional, List, Union
import xml.parsers.expat
from json import dumps, loads

from PyQt5 import QtGui, QtCore
import xmltodict

from spielpendium.logger import set_log_level

__all__ = ['search_bgg', 'get_user_game_collection', 'get_game_info',
           'get_images']

_BGG_API_URL = 'https://www.boardgamegeek.com/xmlapi/'

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

    first_time = True

    while True:
        try:
            with urllib.request.urlopen(url) as file:
                data = file.read()
            if logger is not None:
                logger.debug(f'Information retrieved successfully from {url}.')
        except urllib.error.HTTPError as err:
            if logger is not None:
                logger.error(f'Information was unable to be retrieved from '
                             f'{url}. {err}')
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
                             'at the provided URL.') from None

        if 'message' not in data.keys():
            if logger is not None:
                logger.info(f'Data successfully pulled from {url}.')
            break
        else:
            if logger is not None:
                if first_time:
                    logger.info(f'Waiting for API to generate data at {url}.')
                    first_time = False
                else:
                    logger.info(f'Still waiting for API to generate data.')
            time.sleep(10)

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
    search_url = f'{_BGG_API_URL}search?search={search_query}' \
                 f'&exact={exact_dict[exact_flag]}'

    return get_xml_info(search_url, **kwargs)


def get_user_game_collection(
        username: str,
        filters: Optional[Dict[str, Union[int, bool]]] = None,
        **kwargs
) -> Dict:
    """ Grabs a user's game collection from BGG.

    :param username: The username who's collection were grabbing.
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

    return get_xml_info(collection_url, **kwargs)


def get_game_info(game_id: Union[int, List[int]], **kwargs) -> Dict:
    """ Gets details for a game with a certain game id.

    :param game_id: The BGG game id(s) to get information for.
    :return: The details of the game(s).
    """

    if isinstance(game_id, int):
        game_id = [game_id]

    url = _BGG_API_URL + 'boardgame/' + ','.join([str(a) for a in game_id])

    if 'stats' in kwargs.keys():
        url = url + f'?stats={int(kwargs["stats"])}'

    return get_xml_info(url, **kwargs)


def get_images(image_urls: Union[str, List[str]]) -> List[QtGui.QImage]:
    """ Retrieves images from a list of URLs.

    :param image_urls: The image URLs.
    :return: The images.
    """
    if isinstance(image_urls, str):
        image_urls = [image_urls]

    pool = mp.Pool(processes=mp.cpu_count())
    images_as_bytes = pool.map(get_single_image, image_urls)
    images = [QtGui.QImage.fromData(im).scaled(
        64, 64, QtCore.Qt.KeepAspectRatio
    ) for im in images_as_bytes]

    # for image_url in image_urls:
    #     with urllib.request.urlopen(image_url) as url:
    #         images.append(QtGui.QImage.fromData(url.read()))

    return images


def get_single_image(image_url: str) -> bytes:
    """ Gets the image at the requested url.

    :param image_url: The image url.
    :return: The image as bytes.
    """

    with urllib.request.urlopen(image_url) as url:
        image = url.read()

    return image


if __name__ == '__main__':
    # test_url = 'https://www.boardgamegeek.com/xmlapi/boardgame/35424'
    # test_url = 'https://www.boardgamegeek.com/xmlapi2/boardgame/35424'
    # test_url = 'https://www.google.com'

    # info = get_xml_info(test_url)

    # search_results = search_bgg('Catan')
    # print(dumps(search_results, indent=2))

    collection = get_user_game_collection('phoenix713', filters={'own': True})
    # print(dumps(collection, indent=2))

    # game_details = get_game_info([224125, 255907])
    # print(dumps(game_details, indent=2))

    # test_image = 'https://cf.geekdo-images.com/vpET5JF4hXUXA6bqXx0WlQ__' \
    #              'original/img/FyZogAqdllhWqFns_zfjhaUP6jM=/0x0/' \
    #              'filters:format(jpeg)/pic4854460.jpg'
    # im = get_image(test_image)
    # print(im)
    # im.save('test.png', 'png')
    # print(dumps(info, indent=2))
