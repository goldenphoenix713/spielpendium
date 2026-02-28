"""The BGG API side of the Spielpendium-BGG interface."""

import concurrent.futures
import logging
import time
import urllib.parse
from typing import Any
from uuid import UUID

import requests
import xmltodict
from sqlalchemy.orm import selectinload  # Added for eager loading
from sqlmodel import Session, select

from config import (
    BGG_API_TOKEN,
    BGG_API_URL,
    MAX_API_CHECKS,
    TIME_BETWEEN_API_CHECKS,
)
from util.database.sqlmodel_test import (
    Collection,
    CollectionItem,
    Game,
    OwnershipStatus,
    create_db_and_tables,
    engine,
)

log = logging.getLogger(__name__)


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
    """Pulls XML info from the web and converts it to a dict.

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
            log.info(
                f"Waiting for API to generate data at {url}. "
                f"Next check in {TIME_BETWEEN_API_CHECKS} seconds"
            )
            time.sleep(TIME_BETWEEN_API_CHECKS)
            continue

        # If we reach here, it's not a 202. If it's not 200 either,
        # quit (error)
        if response.status_code != 200:
            log.error(
                f"API did not generate data at {url} after "
                f"checking {MAX_API_CHECKS} times. "
            )
            response.raise_for_status()

        data_bytes = response.content
        log.debug(f"Information retrieved successfully from {url}.")

        # Convert the bytes object to an OrderedDict.
        data = xmltodict.parse(data_bytes)
        log.debug("Data successfully converted to dict.")
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


def user_exists(username: str) -> bool:
    """Checks if a user's collection exists in the database."""
    with Session(engine) as session:
        # We assume a user's existence is tied to having a collection entry
        statement = select(Collection).where(Collection.username == username)
        collection = session.exec(statement).first()
        return collection is not None


def save_collection_data_to_db(username: str, collection_data: dict[str, Any]):
    """
    Saves/updates a user's game collection in the database using SQLModel.
    collection_data is the dict parsed from the BGG API XML response.
    """
    with Session(engine) as session:
        # Find or create the Collection for the user
        collection_statement = select(Collection).where(
            Collection.username == username
        )
        collection = session.exec(collection_statement).first()

        if not collection:
            collection = Collection(
                username=username, name=f"{username}'s Collection"
            )
            session.add(collection)
            session.flush()  # Flush to get the ID for new collection

        # The BGG API collection response structure is usually something like:
        # {'items': {'item': [...game_items...]}}
        bgg_items = collection_data.get("items", {}).get("item", [])
        if not isinstance(
            bgg_items, list
        ):  # Handle single item case from xmltodict
            bgg_items = [bgg_items]

        # For each item in the BGG collection, create/update Game and CollectionItem
        for item_data in bgg_items:
            game_id_str = item_data.get("@objectid")
            if not game_id_str:
                log.warning(
                    f"Skipping collection item without objectid: {item_data}"
                )
                continue

            # Check if game already exists in DB
            # Assuming BGG game ID can be converted to UUID bytes (e.g., int -> UUID -> bytes)
            # This is a critical assumption about the Game.id field type.
            game_uuid_bytes = UUID(int=int(game_id_str)).bytes
            game_statement = select(Game).where(Game.id == game_uuid_bytes)
            game = session.exec(game_statement).first()

            if not game:
                # If game doesn't exist, we'll need to fetch its full details later
                # For now, just create a minimal Game object
                game_name = item_data.get("name", {}).get(
                    "#text", f"Unknown Game {game_id_str}"
                )
                game = Game(
                    id=game_uuid_bytes,
                    name=game_name,
                    version=0.0,  # Placeholder
                    image=b"",  # Placeholder
                    description="",  # Placeholder
                    release_year=0,  # Placeholder
                    min_players=0,
                    max_players=0,
                    min_age=0,
                    min_play_time=0,
                    max_play_time=0,
                    complexity=0.0,
                )
                session.add(game)
                session.flush()

            # Find or create OwnershipStatus (e.g., "owned", "want", "prevowned")
            # The BGG API collection XML typically has status attributes like:
            # <status own="1" prevowned="0" ... />
            # We'll need to derive the status name from these.
            # For simplicity, if 'own' is true, we set to "owned".
            # The prompt's suggested code sets it to "owned" by default,
            # which might be too simplistic if other statuses are important.
            # Sticking to suggested code for now, using "owned".
            status_name = "owned"
            if item_data.get("status", {}).get("@want") == "1":
                status_name = "want"
            elif item_data.get("status", {}).get("@prevowned") == "1":
                status_name = "prevowned"
            # Add more status checks here if needed based on `item_data['status']`

            status_statement = select(OwnershipStatus).where(
                OwnershipStatus.name == status_name
            )
            ownership_status = session.exec(status_statement).first()
            if not ownership_status:
                ownership_status = OwnershipStatus(name=status_name)
                session.add(ownership_status)
                session.flush()

            # Find or create CollectionItem
            item_statement = select(CollectionItem).where(
                CollectionItem.collection_id == collection.id,
                CollectionItem.game_id == game.id,
            )
            collection_item = session.exec(item_statement).first()

            if not collection_item:
                collection_item = CollectionItem(
                    collection_id=collection.id,
                    game_id=game.id,
                    ownership_status_id=ownership_status.id,
                )
                session.add(collection_item)
            else:
                # Update existing item if needed (e.g., status changed)
                collection_item.ownership_status_id = ownership_status.id

        session.commit()
        log.info(f"Collection for user {username} saved/updated in DB.")


def get_user_collection_from_db(username: str) -> Collection | None:
    """Retrieves a user's collection from the database using SQLModel."""
    with Session(engine) as session:
        statement = (
            select(Collection)
            .where(Collection.username == username)
            .options(
                # Using selectinload for eager loading as Relationship.of_type isn't standard
                selectinload(Collection.items).selectinload(
                    CollectionItem.game
                ),
                selectinload(Collection.items).selectinload(
                    CollectionItem.ownership_status
                ),
            )
        )
        collect = session.exec(statement).first()
        return collect


def get_user_game_collection(
    username: str,
    filters: dict[str, int | bool] | None = None,
    force_update: bool = False,
) -> Collection | None:  # Changed return type to Collection model
    """Grabs a user's game collection from BGG or the database.

    :param username: The username whose collection were grabbing.
    :param filters: Additional filters for the game collection.
    :param force_update: Whether to force an update from the API
    :return: A SQLModel Collection object or None if not found.
    """
    collection_from_db = None
    if not force_update:
        collection_from_db = get_user_collection_from_db(username)

    if collection_from_db and not force_update:
        log.info(f"Collection for {username} loaded from database.")
        return collection_from_db
    else:
        log.info(f"Fetching collection for {username} from BGG API.")
        username_safe = urllib.parse.quote(username)
        collection_url = f"{BGG_API_URL}collection"

        query_params = {"username": username_safe, "stats": "1"}

        if filters is not None:
            if any(key not in COLLECTION_FILTERS for key in filters):
                raise KeyError(
                    "Invalid filter provided. Filters must be "
                    'one of the following: "'
                    + '", "'.join(list(COLLECTION_FILTERS))
                    + '".'
                )
            for key, value in filters.items():
                query_params[key] = (
                    str(int(value))
                    if isinstance(value, bool)
                    else (str(value))
                )

        info_dict, xml_raw = get_xml_info(collection_url, query=query_params)
        save_collection_data_to_db(username, info_dict)

        # After saving, retrieve the updated collection from the DB
        return get_user_collection_from_db(username)


def get_game_info(
    game_ids: int | list[int],
    get_stats: bool = False,
) -> dict[str, Any]:
    """Gets details for a game with a certain game id.

    :param game_ids: The BGG game id(s) to get information for.
    :param get_stats: Whether to get detailed game stats or not.
    :return: The details of the game(s).
    """

    # Convert to list
    if isinstance(game_ids, int):
        game_ids = [game_ids]

    # Generate the url (BGG API v2 'thing' endpoint for game details)
    url = BGG_API_URL + "thing"  # Base URL for thing (game/expansion)
    query = {"id": ",".join([str(a) for a in game_ids])}

    if get_stats:
        query["stats"] = "1"

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
    create_db_and_tables()  # Ensure DB tables exist

    # Example: Get user collection
    # Note: The output will now be a SQLModel Collection object, not a raw dict.
    # You might need to adjust how you print it or convert it to dict for display.
    collection = get_user_game_collection(
        "phoenix713", filters={"own": True}, force_update=True
    )
    if collection:
        print("\n--- Collection from SQLModel ---")
        print(
            f"Collection ID: {UUID(bytes=collection.id)}"
        )  # Convert bytes UUID back to readable UUID
        print(f"Username: {collection.username}")
        print(f"Collection Name: {collection.name}")
        for item in collection.items:
            # Need to handle potential None if relationships aren't loaded or data is incomplete
            gamename = item.game.name if item.game else "N/A"
            ownership_status_name = (
                item.ownership_status.name if item.ownership_status else "N/A"
            )
            print(
                f"  - Game: {gamename} (Owned Status: {ownership_status_name})"
            )
    else:
        print("Collection not found or could not be fetched.")

    # test_url = "https://www.boardgamegeek.com/xmlapi/boardgame/35424" # Old API endpoint
    # info = get_xml_info(test_url)
    # print(dumps(info, indent=2))
    #
    # search_results = search_bgg('Catan')
    # print(dumps(search_results, indent=2))
    #
    # game_details = get_game_info([224125, 255907])
    # print(dumps(game_details, indent=2))
    #
    # test_image = ('https://cf.geekdo-images.com/vpET5JF4hXUXA6bqXx0WlQ__'
    #               'original/img/FyZogAqdllhWqFns_zfjhaUP6jM=/0x0/filters:'
    #               'format(jpeg)/pic4854460.jpg')
    # images = get_images(test_image)
    # print(images)
    # images[0].save('test.png', 'png')
