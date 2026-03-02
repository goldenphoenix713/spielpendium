"""The BGG API side of the Spielpendium-BGG interface."""

from __future__ import annotations

import concurrent.futures
import time
import urllib.parse
from typing import TYPE_CHECKING, Any
from xml.parsers.expat import ExpatError

import requests
import xmltodict
from bs4 import BeautifulSoup
from loguru import logger as log
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from config import (
    BGG_API_TOKEN,
    BGG_API_URL,
    MAX_API_CHECKS,
    TIME_BETWEEN_API_CHECKS,
)
from util.database.models import (
    Category,
    Collection,
    CollectionItem,
    Game,
    GameCategoryLink,
    GameRelationship,
    OwnershipStatus,
    Person,
    PersonGameLink,
    PersonRole,
    Publisher,
    PublisherGameLink,
    RelatedGame,
    create_db_and_tables,
    engine,
)

if TYPE_CHECKING:
    from sqlmodel import SQLModel

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
) -> dict[str, Any]:
    """Pulls XML info from the web and converts it to a dict.

    :param url: The URL that will be pulled to get XML data.
    :type url: str
    :param query: A dictionary containing query parameters for the get request.
    :type query: dict[str, str]
    :raises requests.exceptions.HTTPError: If there's any error in retrieving
            data at the URL.
    :raises xmltodict.expat.ExpatError: If the retrieved data cannot be
            converted to a dict
    :return: The information from the XML converted into a dict.
    :rtype: dict[str, Any]
    """

    data: dict[str, Any] = {}

    for ii in range(MAX_API_CHECKS):
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

        # Convert the bytes object to a dict.
        try:
            data = xmltodict.parse(data_bytes)
            log.debug("Data successfully converted to dict.")
            return data
        except ExpatError as e:
            log.error(f"Failed to parse XML from {url}: {e}.")
            if ii < MAX_API_CHECKS - 1:
                time.sleep(TIME_BETWEEN_API_CHECKS)
                continue
            else:
                raise

    return data


def search_bgg(search_query: str, exact_flag: bool = False) -> dict[str, Any]:
    """Assembles the search URL and returns data from the BoardGameGeek API.

    :param search_query: The query to search for.
    :type search_query: str
    :param exact_flag: A flag that tells the BGG API whether to only return
        exact matches or not.
    :type exact_flag: bool
    :return: Dictionary with the search results.
    :rtype: dict[str, Any]
    """
    search_query = urllib.parse.quote(search_query)
    search_url = f"{BGG_API_URL}search"

    query = {"query": search_query, "exact": str(int(exact_flag))}
    return get_xml_info(search_url, query)


def user_exists_in_db(username: str) -> bool:
    """Checks if a user's collection exists in the database.

    :param username: The username to check in the database.
    :type username: str
    :return: Whether the user's collection was found in the db.
    :rtype: bool
    """
    with Session(engine) as session:
        # We assume a user's existence is tied to having a collection entry
        statement = select(Collection).where(Collection.username == username)
        collection = session.exec(statement).first()
        return collection is not None


def _process_and_save_game_details(
    session: Session, bgg_id: int, game_detail_data: dict[str, Any]
) -> Game | None:
    """Helper function to process detailed game data from BGG API.

    :param session: The SQLModel session to use.
    :param bgg_id: The BGG ID of the game.
    :param game_detail_data: The dictionary parsed from the BGG API response.
    :return: The saved or updated Game object, or None if processing fails.
    """
    items_data = game_detail_data.get("items", {})
    game_item_data = items_data.get("item")

    if not game_item_data:
        log.error(f"No game item data found for bgg_id: {bgg_id} in response.")
        return None

    if isinstance(game_item_data, list):
        if len(game_item_data) > 1:
            log.warning(
                f"Multiple items returned for bgg_id {bgg_id}. "
                "Processing only the first."
            )
        game_item_data = game_item_data[0]

    game_statement = select(Game).where(Game.bgg_id == bgg_id)
    game = session.exec(game_statement).first()

    if not game:
        game = Game(bgg_id=bgg_id)
        session.add(game)
        session.flush()

    # --- Populate Game fields ---
    names = game_item_data.get("name")
    if isinstance(names, list):
        primary_name = next(
            (n["#text"] for n in names if n.get("@type") == "primary"), None
        )
        game.name = primary_name or (
            names[0]["#text"] if names else f"Unknown Game {bgg_id}"
        )
    elif isinstance(names, dict):
        game.name = (
            names.get("#text")
            or names.get("@value")
            or f"Unknown Game {bgg_id}"
        )
    else:
        game.name = f"Unknown Game {bgg_id}"

    game.sub_name = (
        next(
            (n["#text"] for n in names if n.get("@type") == "alternate"), None
        )
        if isinstance(names, list)
        else None
    )

    game.version = float(
        game_item_data.get("yearpublished", {}).get("@value", 0)
    )

    # Placeholder for image fetching
    game.image = b""

    game.description = game_item_data.get("description", "") or ""
    if (
        game.description
        and "<" in game.description
        and ">" in game.description
    ):
        soup = BeautifulSoup(game.description, "html.parser")
        game.description = soup.get_text()

    game.release_year = int(
        game_item_data.get("yearpublished", {}).get("@value", 0)
    )

    game.min_players = int(
        game_item_data.get("minplayers", {}).get("@value", 0)
    )
    game.max_players = int(
        game_item_data.get("maxplayers", {}).get("@value", 0)
    )
    game.min_age = int(game_item_data.get("minage", {}).get("@value", 0))
    game.min_play_time = int(
        game_item_data.get("minplaytime", {}).get("@value", 0)
    )
    game.max_play_time = int(
        game_item_data.get("maxplaytime", {}).get("@value", 0)
    )

    # Stats and Ranks
    ratings = game_item_data.get("statistics", {}).get("ratings", {})
    game.bgg_rating = float(ratings.get("average", {}).get("@value", 0.0))

    ranks = ratings.get("ranks", {}).get("rank", [])
    if isinstance(ranks, dict):
        ranks = [ranks]
    boardgame_rank_value = next(
        (r.get("@value") for r in ranks if r.get("@name") == "boardgame"),
        "N/A",
    )
    game.bgg_rank = (
        int(boardgame_rank_value)
        if boardgame_rank_value not in ["N/A", None]
        else None
    )

    game.complexity = float(
        ratings.get("averageweight", {}).get("@value", 0.0)
    )
    game.recommended_players = None

    session.add(game)

    # Helper to get/create entity and link
    def get_or_create_entity_and_link(
        sess: Session,
        model: type[SQLModel],
        link_model: type[SQLModel],
        entity_name_key: str,
        link_entity_id_attr: str,
        link_game_id_attr: str,
        bgg_data_list: list[dict[str, Any]],
        role_id: bytes | None = None,
    ) -> None:
        for data in bgg_data_list:
            item_name = data.get("#text") or data.get("@value")
            if not item_name:
                continue

            entity_statement = select(model).where(model.name == item_name)  # type: ignore[attr-defined]
            entity = sess.exec(entity_statement).first()
            if not entity:
                entity = model(name=item_name)
                sess.add(entity)
                sess.flush()

            link_exists_statement = select(link_model).where(
                getattr(link_model, link_entity_id_attr) == entity.id,  # type: ignore[attr-defined]
                getattr(link_model, link_game_id_attr) == game.id,
            )
            if role_id:
                link_exists_statement = link_exists_statement.where(
                    PersonGameLink.role_id == role_id
                )

            if not sess.exec(link_exists_statement).first():
                link_kwargs = {
                    link_entity_id_attr: entity.id,  # type: ignore[attr-defined]
                    link_game_id_attr: game.id,
                }
                if role_id:
                    link_kwargs["role_id"] = role_id
                sess.add(link_model(**link_kwargs))

    # Publishers
    publishers_data = game_item_data.get("boardgamepublisher", [])
    if isinstance(publishers_data, dict):
        publishers_data = [publishers_data]
    get_or_create_entity_and_link(
        session,
        Publisher,
        PublisherGameLink,
        "name",
        "publisher_id",
        "game_id",
        publishers_data,
    )

    # Categories
    categories_data = game_item_data.get("boardgamecategory", [])
    if isinstance(categories_data, dict):
        categories_data = [categories_data]
    get_or_create_entity_and_link(
        session,
        Category,
        GameCategoryLink,
        "name",
        "category_id",
        "game_id",
        categories_data,
    )

    # Persons
    author_role = session.exec(
        select(PersonRole).where(PersonRole.role == "author")
    ).first()
    if not author_role:
        author_role = PersonRole(role="author")
        session.add(author_role)
        session.flush()

    artist_role = session.exec(
        select(PersonRole).where(PersonRole.role == "artist")
    ).first()
    if not artist_role:
        artist_role = PersonRole(role="artist")
        session.add(artist_role)
        session.flush()

    designers_data = game_item_data.get("boardgamedesigner", [])
    if isinstance(designers_data, dict):
        designers_data = [designers_data]
    get_or_create_entity_and_link(
        session,
        Person,
        PersonGameLink,
        "name",
        "person_id",
        "game_id",
        designers_data,
        role_id=author_role.id,
    )

    artists_data = game_item_data.get("boardgameartist", [])
    if isinstance(artists_data, dict):
        artists_data = [artists_data]
    get_or_create_entity_and_link(
        session,
        Person,
        PersonGameLink,
        "name",
        "person_id",
        "game_id",
        artists_data,
        role_id=artist_role.id,
    )

    # Related Games
    for link_type_key in [
        "boardgameexpansion",
        "boardgamereimplementation",
        "boardgameaccessory",
        "boardgamecompilation",
    ]:
        linked_items = game_item_data.get(link_type_key, [])
        if isinstance(linked_items, dict):
            linked_items = [linked_items]

        if not linked_items:
            continue

        relationship_type_name = link_type_key.replace(
            "boardgame", ""
        ).replace("item", "")
        relationship_type_statement = select(GameRelationship).where(
            GameRelationship.type == relationship_type_name
        )
        relationship_type = session.exec(relationship_type_statement).first()
        if not relationship_type:
            relationship_type = GameRelationship(type=relationship_type_name)
            session.add(relationship_type)
            session.flush()

        for linked_item_data in linked_items:
            target_bgg_id_str = linked_item_data.get("@objectid")
            if not target_bgg_id_str:
                continue
            target_bgg_id = int(target_bgg_id_str)

            target_game_statement = select(Game).where(
                Game.bgg_id == target_bgg_id
            )
            target_game = session.exec(target_game_statement).first()
            if not target_game:
                target_game = Game(
                    bgg_id=target_bgg_id,
                    name=linked_item_data.get("#text")
                    or f"Related Game {target_bgg_id}",
                    version=0.0,
                    image=b"",
                    description="",
                    release_year=0,
                    min_players=0,
                    max_players=0,
                    min_age=0,
                    min_play_time=0,
                    max_play_time=0,
                    complexity=0.0,
                )
                session.add(target_game)
                session.flush()

            related_link_statement = select(RelatedGame).where(
                RelatedGame.source_game_id == game.id,
                RelatedGame.target_game_id == target_game.id,
                RelatedGame.relationship_type_id == relationship_type.id,
            )
            if not session.exec(related_link_statement).first():
                session.add(
                    RelatedGame(
                        source_game_id=game.id,
                        target_game_id=target_game.id,
                        relationship_type_id=relationship_type.id,
                    )
                )

    return game


def save_collection_data_to_db(
    username: str, collection_data: dict[str, Any]
) -> None:
    """Saves/updates a user's game collection in the database.

    :param username: The username for the owner of the collection.
    :type username: str
    :param collection_data: The user's collection data returned from the BGG
                            API XML response.
    :type collection_data: dict[str, Any]
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
        if not isinstance(bgg_items, list):
            # Handle single item case from xmltodict
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
            bgg_id = int(game_id_str)
            game_statement = select(Game).where(Game.bgg_id == bgg_id)
            game = session.exec(game_statement).first()

            if not game:
                # If game doesn't exist, we'll need to fetch its full details later
                # For now, just create a minimal Game object
                game_name = item_data.get("name", {}).get(
                    "#text", f"Unknown Game {game_id_str}"
                )
                game = Game(
                    bgg_id=bgg_id,
                    name=game_name,
                    version=0.0,  # Placeholder
                    image=b"",  # Placeholder
                    description="",  # Placeholder
                    release_year=0,  # Placeholder
                    min_players=0,  # Placeholder
                    max_players=0,  # Placeholder
                    min_age=0,  # Placeholder
                    min_play_time=0,  # Placeholder
                    max_play_time=0,  # Placeholder
                    complexity=0.0,  # Placeholder
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
    """Retrieves a user's collection from the database using SQLModel.

    :param username: The username of collection owner.
    :type username: str
    :return: The collection, if it exists in the db, otherwise None
    :rtype: Collection | None
    """
    with Session(engine) as session:
        statement = (
            select(Collection)
            .where(Collection.username == username)
            .options(
                # Using selectinload for eager loading as Relationship.of_type isn't standard
                selectinload(Collection.items).selectinload(  # type: ignore[arg-type]
                    CollectionItem.game  # type: ignore[arg-type]
                ),
                selectinload(Collection.items).selectinload(  # type: ignore[arg-type]
                    CollectionItem.ownership_status  # type: ignore[arg-type]
                ),
            )
        )
        collect = session.exec(statement).first()
        return collect


def get_user_game_collection(
    username: str,
    filters: dict[str, int | bool] | None = None,
    force_update: bool = False,
) -> Collection | None:
    """Grabs a user's game collection from BGG or the database.

    :param username: The username whose collection were grabbing.
    :type username: str
    :param filters: Additional filters for the game collection.
    :type filters: dict[str, int | bool]
    :param force_update: Whether to force an update from the API
    :type force_update: bool
    :return: A SQLModel Collection object or None if not found.
    :rtype: Collection | None
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

        info_dict = get_xml_info(collection_url, query=query_params)
        save_collection_data_to_db(username, info_dict)

        # After saving, retrieve the updated collection from the DB
        return get_user_collection_from_db(username)


def get_game_info(
    game_ids: int | list[int],
    get_stats: bool = False,
    get_versions: bool = False,
    get_videos: bool = False,
    get_comments: bool = False,
    get_marketplacelistings: bool = False,
    get_trading: bool = False,
    get_want: bool = False,
    get_rank: bool = False,
    get_image_list: bool = False,
) -> dict[str, Any]:
    """Gets details for a game with a certain game id.

    :param game_ids: The BGG game id(s) to get information for.
    :type game_ids: int | list[int]
    :param get_stats: Whether to get detailed game stats or not.
    :type get_stats: bool
    :param get_versions: Whether to include versions data.
    :type get_versions: bool
    :param get_videos: Whether to include videos data.
    :type get_videos: bool
    :param get_comments: Whether to include comments data.
    :type get_comments: bool
    :param get_marketplacelistings: Whether to include marketplace listings.
    :type get_marketplacelistings: bool
    :param get_trading: Whether to include trading data.
    :type get_trading: bool
    :param get_want: Whether to include 'want' data.
    :type get_want: bool
    :param get_rank: Whether to include rank data.
    :type get_rank: bool
    :param get_image_list: Whether to include images data.
    :type get_image_list: bool
    :return: The details of the game(s) as a dictionary parsed from an XML.
    :rtype: dict[str, Any]
    """

    # Convert to list
    if isinstance(game_ids, int):
        game_ids = [game_ids]

    # Generate the url (BGG API v2 'thing' endpoint for game details)
    url = BGG_API_URL + "thing"  # Base URL for thing (game/expansion)
    query = {
        "id": ",".join([str(a) for a in game_ids]),
        "stats": "1" if get_stats else "0",
        "versions": "1" if get_versions else "0",
        "videos": "1" if get_videos else "0",
        "comments": "1" if get_comments else "0",
        "marketplacelistings": "1" if get_marketplacelistings else "0",
        "trading": "1" if get_trading else "0",
        "want": "1" if get_want else "0",
        "rank": "1" if get_rank else "0",
        "images": "1" if get_image_list else "0",
    }

    # Clean up '0' values to avoid sending unnecessary query parameters
    query = {k: v for k, v in query.items() if v != "0"}

    # TODO BGG API Limits "thing" searches to 20 items at a time.
    #  Need to add a limiter here.

    return get_xml_info(url, query=query)


def get_images(image_urls: str | list[str]) -> list[bytes]:
    """Retrieves images from a list of URLs.

    :param image_urls: The image URLs.
    :type image_urls: str | list[str]
    :return: The images as a list of bytes.
    :rtype: list[bytes]
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
            executor.submit(get_single_image, url, 60.0, session): url
            for url in image_urls
        }
        images = [
            future.result()
            for future in concurrent.futures.as_completed(future_to_url)
        ]

    return images


def get_single_image(
    image_url: str, timeout: float, session: requests.Session
) -> bytes:
    """Gets the image at the requested url.

    :param image_url: The image url.
    :type image_url: str
    :param timeout: The timeout in seconds.
    :type timeout: float
    :param session: The session to use.
    :return: The image bytes.
    :rtype: bytes
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
    from uuid import UUID

    create_db_and_tables()  # Ensure DB tables exist

    # Example: Get user collection
    # Note: The output will now be a SQLModel Collection object, not a raw dict.
    # You might need to adjust how you print it or convert it to dict for display.
    user_collection = get_user_game_collection(
        "phoenix713", filters={"own": True}, force_update=True
    )
    if user_collection:
        print("\n--- Collection from SQLModel ---")
        print(
            f"Collection ID: {UUID(bytes=user_collection.id)}"
        )  # Convert bytes UUID back to readable UUID
        print(f"Username: {user_collection.username}")
        print(f"Collection Name: {user_collection.name}")
        for item in user_collection.items:
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
