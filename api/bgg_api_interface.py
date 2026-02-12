"""The BGG API side of the Spielpendium-BGG interface."""

import concurrent.futures
import time
import urllib.parse

import requests
import xmltodict

import log
from config import (
    BGG_API_TOKEN,
    BGG_API_URL,
    MAX_API_CHECKS,
    TIME_BETWEEN_API_CHECKS,
)
from util import database
from util.database.scripts import SQLScripts

__author__ = "Eduardo Ruiz"

__all__ = [
    "search_bgg",
    "get_user_game_collection",
    "get_game_info",
    "get_images",
]

# noinspection SpellCheckingInspection
COLLECTION_FILTERS = (
    "own",
    "rated",
    "played",
    "comment",
    "trade",
    "want",
    "wantintrade",
    "wishlist",
    "wanttoplay",
    "wanttobuy",
    "prevowned",
    "preordered",
    "hasparts",
    "wantparts",
    "notifycontent",
    "notifysale",
    "notifyaution",
    "wishlistpriority",
    "minrating",
    "maxrating",
    "minbggrating",
    "maxbggrating",
    "minplays",
    "maxplays",
    "showprivate",
)


def get_xml_info(
    url: str, query: dict[str, str] | None = None
) -> tuple[dict[str, str], str]:
    """Pulls xml info from the web and converts it to a dict.

    :param url: The URL that will be pulled to get XML data.
    :param query: A dictionary containing query parameters for the get request.
    :raises urllib.error.HTTPError: If there's any error in retrieving data at
            the URL.
    :raises ValueError: If the retrieved data cannot be converted to a dict
    :return: The information from the XML converted into a dict.
    """

    data = {}
    data_bytes = b""

    for _ in range(MAX_API_CHECKS):
        with requests.session() as session:
            response = session.get(
                url,
                params=query,
                headers={"Authorization": f"Bearer {BGG_API_TOKEN}"},
            )
        # Code 202 means data is still being generated
        if response.status_code == 202:
            log.logger.info(
                f"Waiting for API to generate data at {url}. "
                f"Next check in {TIME_BETWEEN_API_CHECKS} seconds"
            )
            time.sleep(TIME_BETWEEN_API_CHECKS)
            continue

        # If we reach here, it's not a 202. If it's not 200 either,
        # quit (error)
        if response.status_code != 200:
            log.logger.error(
                f"API did not generate data at {url} after "
                f"checking {MAX_API_CHECKS} times. "
            )
            response.raise_for_status()

        data_bytes = response.content
        log.logger.debug(f"Information retrieved successfully from {url}.")

        # Convert the bytes object to an OrderedDict.
        data = xmltodict.parse(data_bytes)
        log.logger.debug("Data successfully converted to dict.")
        break

    return data, data_bytes.decode()


def search_bgg(search_query: str, exact_flag: bool = False) -> dict[str, str]:
    """Assembles the search URL and returns data from the BoardGameGeek API.

    :param search_query: The query to search for.
    :param exact_flag: A flag that tells the BGG API whether to only return
           exact matches or not.
    :return: Dictionary with the search results
    """
    search_query = urllib.parse.quote(search_query)
    search_url = f"{BGG_API_URL}search"

    query = {"search": search_query, "exact": str(int(exact_flag))}
    return get_xml_info(search_url, query)[0]


def get_user_game_collection(
    username: str,
    filters: dict[str, int | bool] | None = None,
    force_update: bool = False,
) -> dict[str, str]:
    """Grabs a user's game collection from BGG.

    :param username: The username whose collection were grabbing.
    :param filters: Additional filters for the game collection.
    :param force_update: Whether to force an update from the API
    :return: A dictionary with the user's game collection.
    """

    if user_exists(username) and not force_update:
        info_dict = get_user_info(username)
    else:
        username_safe = urllib.parse.quote(username)
        collection_url = f"{BGG_API_URL}collection/{username_safe}"

        if filters is not None:
            if any(key not in COLLECTION_FILTERS for key in filters):
                raise KeyError(
                    "Invalid filter provided. Filters must be "
                    'one of the following: "'
                    + '", "'.join(list(COLLECTION_FILTERS))
                    + '".'
                )

            query = {key: str(int(value)) for key, value in filters.items()}
        else:
            query = None

        info_dict, xml = get_xml_info(collection_url, query=query)

        save_user_xml(username, xml)

    return info_dict


def get_user_info(username: str) -> dict[str, str]:
    command = SQLScripts.get_user_xml
    with database.SqliteDB() as db:
        db.execute(command, (username,))
        xml = db.fetchone()[0]

    return xmltodict.parse(xml)


def user_exists(username: str) -> bool:
    command = SQLScripts.user_exists
    with database.SqliteDB() as db:
        db.execute(command, [username])
        return db.fetchone()[0] == 1


def save_user_xml(username: str, xml: str):
    command = SQLScripts.save_user_xml
    with database.SqliteDB() as db:
        db.execute(command, [username, xml])


def get_game_info(
    game_ids: int | list[int],
    get_stats: bool = False,
) -> dict[str, str]:
    """Gets details for a game with a certain game id.

    :param game_ids: The BGG game id(s) to get information for.
    :param get_stats: Whether to get detailed game stats or not.
    :return: The details of the game(s).
    """

    # Convert to list
    if isinstance(game_ids, int):
        game_ids = [game_ids]

    # Generate the url
    url = BGG_API_URL + "boardgame/" + ",".join([str(a) for a in game_ids])
    query = {"stats": "1"} if get_stats else None

    return get_xml_info(url, query=query)[0]


def get_images(image_urls: str | list[str]) -> list[bytes]:
    """Retrieves images from a list of URLs.

    :param image_urls: The image URLs.
    :return: The images.
    """
    # Convert to list
    if isinstance(image_urls, str):
        image_urls = [image_urls]

    # Set up pool of subprocesses to each get an image
    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor,
        requests.Session() as session,
    ):
        # Start the load operations and mark each future with its URL
        future_to_url = {
            executor.submit(get_single_image, url, 60, session): url
            for url in image_urls
        }
        images = [
            future.result()
            for future in concurrent.futures.as_completed(future_to_url)
        ]

    return images


def get_single_image(
    image_url: str, timeout: int, session: requests.Session
) -> bytes:
    """Gets the image at the requested url.

    :param image_url: The image url.
    :param timeout: The timeout in seconds.
    :param session: The session to use.
    :return: The image as bytes.
    """

    response = session.get(
        image_url,
        headers={"Authorization": f"Bearer {BGG_API_TOKEN}"},
        timeout=timeout,
    )

    if response.status_code == 200:
        image = response.content
    else:
        raise requests.exceptions.Timeout

    return image


if __name__ == "__main__":
    from json import dumps

    # test_url = "https://www.boardgamegeek.com/xmlapi/boardgame/35424"
    # info = get_xml_info(test_url)
    # print(dumps(info, indent=2))
    #
    # search_results = search_bgg('Catan')
    # print(dumps(search_results, indent=2))
    #
    collection = get_user_game_collection(
        "phoenix713", filters={"own": True}, force_update=False
    )
    print(dumps(collection, indent=2))

    # game_details = get_game_info([224125, 255907])
    # print(dumps(game_details, indent=2))
    #
    # test_image = ('https://cf.geekdo-images.com/vpET5JF4hXUXA6bqXx0WlQ__'
    #               'original/img/FyZogAqdllhWqFns_zfjhaUP6jM=/0x0/filters:'
    #               'format(jpeg)/pic4854460.jpg')
    # images = get_images(test_image)
    # print(images)
    # images[0].save('test.png', 'png')
