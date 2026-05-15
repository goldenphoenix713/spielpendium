"""Collection handling for the BoardGameGeek API."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from loguru import logger as log
from sqlalchemy.orm import selectinload
from sqlmodel import Session as SQLModelSession
from sqlmodel import select

from config import BGG_API_URL
from util.models import (
    Collection,
    CollectionItem,
    Game,
    OwnershipStatus,
    engine,
)

from .client import get_xml_info
from .game_details import _process_and_save_game_details, get_game_info
from .images import get_images

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


def user_exists_in_db(username: str) -> bool:
    """Checks if a user's collection exists in the database.

    :param username: The username to check in the database.
    :type username: str
    :return: Whether the user's collection was found in the db.
    :rtype: bool
    """
    with SQLModelSession(engine) as session:
        # We assume a user's existence is tied to having a collection entry
        statement = select(Collection).where(Collection.username == username)
        collection = session.exec(statement).first()
        return collection is not None


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
    # TODO Add a progress bar instead of the loading overlay
    with SQLModelSession(engine) as session:
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
            session.flush()

        items_data = collection_data.get("items", {})

        # "item" can be a list or a single dict
        bgg_items = items_data.get("item", [])
        if isinstance(bgg_items, dict):
            bgg_items = [bgg_items]

        # Extract all game IDs
        game_ids = []
        for item in bgg_items:
            bgg_id_str = item.get("@objectid")
            if bgg_id_str:
                game_ids.append(int(bgg_id_str))

        if not game_ids:
            log.warning(f"No games found in collection for user {username}")
            return

        # Fetch detailed data for all games in the collection at once in batches of 20
        # (BGG limit is generally ~20 per "thing" request)
        batch_size = 20
        for i in range(0, len(game_ids), batch_size):
            batch_ids = game_ids[i : i + batch_size]
            log.info(
                f"Fetching detailed data for batch of games ({i + 1} to "
                f"{min(i + batch_size, len(game_ids))} / {len(game_ids)})..."
            )

            # Retrieve details (stats, videos, relations, images, etc.)
            game_details_api_response = get_game_info(
                batch_ids,
                get_stats=True,
                get_versions=False,
                get_videos=True,
                get_comments=True,
                get_marketplacelistings=True,
                get_trading=True,
                get_want=True,
                get_rank=True,
                get_image_list=True,
            )

            # Process the batch response
            items_data = game_details_api_response.get("items", {})
            game_items = items_data.get("item", [])
            if isinstance(game_items, dict):
                game_items = [game_items]

            images_to_download: list[tuple[int, str]] = []

            for g_item in game_items:
                # Wrap each item in a structure compatible with _process_and_save_game_details
                single_game_data = {"items": {"item": g_item}}
                bgg_id_val = int(g_item.get("@id", 0))
                g_obj, g_img_url = _process_and_save_game_details(
                    session, bgg_id_val, single_game_data
                )
                if g_obj and g_img_url:
                    images_to_download.append((bgg_id_val, g_img_url))

            if images_to_download:
                log.info(
                    f"Batch downloading {len(images_to_download)} images..."
                )
                saved_images_dict = get_images(images_to_download)
                # Update the games with the new image paths
                for bgg_id_val, image_path in saved_images_dict.items():
                    if image_path:
                        game_statement = select(Game).where(
                            Game.bgg_id == bgg_id_val
                        )
                        g_obj = session.exec(game_statement).first()
                        if g_obj:
                            g_obj.image_path = image_path
                session.commit()

        # Re-iterate items to create CollectionItems
        for item_data in bgg_items:
            bgg_id_str = item_data.get("@objectid")
            if not bgg_id_str:
                log.warning(
                    f"Skipping collection item without objectid: {item_data}"
                )
                continue

            current_bgg_id = int(bgg_id_str)

            game_statement = select(Game).where(Game.bgg_id == current_bgg_id)
            game = session.exec(game_statement).first()

            if not game:
                log.error(
                    f"Game with BGG ID {current_bgg_id} still missing after batch fetch."
                )
                continue

            # Find or create OwnershipStatus (e.g., "owned", "want", "prevowned")
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
                ownership_status = OwnershipStatus(
                    id=uuid4().bytes, name=status_name
                )
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
    with SQLModelSession(engine) as session:
        statement = (
            select(Collection)
            .where(Collection.username == username)
            .options(
                selectinload(Collection.items)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                .selectinload(  # type: ignore[arg-type]
                    CollectionItem.game  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                )
                .selectinload(  # type: ignore[arg-type]
                    Game.categories  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                ),
                selectinload(Collection.items).selectinload(  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                    CollectionItem.ownership_status  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                ),
            )
        )
        collect: Collection | None = session.exec(statement).first()
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
    :param force_update: Whether to force an update from the BGG API.
    :type force_update: bool
    :return: A SQLModel Collection object or None if not found.
    :rtype: Collection | None
    """
    if filters:
        for key in filters:
            if key not in COLLECTION_FILTERS:
                raise ValueError(
                    f"Invalid filter: {key}. Collection filter options: "
                    f"{COLLECTION_FILTERS}"
                )
    else:
        filters = {"own": 1}

    # Only convert bools to 1 or 0 string reps
    string_filters = {
        k: str(int(v)) if isinstance(v, bool) else str(v)
        for k, v in filters.items()
    }
    string_filters.update({"username": username})

    db_collection = get_user_collection_from_db(username)

    if db_collection and not force_update:
        log.info(
            f"Retrieving collection for user '{username}' from local database."
        )
        return db_collection

    url = f"{BGG_API_URL}collection"

    log.info(f"Fetching collection for user '{username}' from BGG API.")
    data = get_xml_info(url, string_filters)

    if not data:
        log.warning(f"No collection data found from BGG for user: {username}")
        return None

    # Save the newly fetched data
    save_collection_data_to_db(username, data)

    # Return the newly saved collection from DB
    return get_user_collection_from_db(username)
