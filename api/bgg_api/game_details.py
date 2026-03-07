"""Game detail fetching logic for the BoardGameGeek API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from loguru import logger as log
from sqlmodel import select

from config import BGG_API_URL
from util.models import (
    Category,
    Game,
    GameCategoryLink,
    GameRelationship,
    Person,
    PersonGameLink,
    PersonRole,
    Publisher,
    PublisherGameLink,
    RelatedGame,
)

from .client import get_xml_info

if TYPE_CHECKING:
    from typing import TypeVar

    from sqlmodel import Session as SQLModelSession
    from sqlmodel import SQLModel

    TModel = TypeVar("TModel", bound=SQLModel)
    TLink = TypeVar("TLink", bound=SQLModel)


def _process_and_save_game_details(
    session: SQLModelSession, bgg_id: int, game_detail_data: dict[str, Any]
) -> tuple[Game | None, str | None]:
    """Helper function to process detailed game data from BGG API.

    :param session: The SQLModel session to use.
    :param bgg_id: The BGG ID of the game.
    :param game_detail_data: The dictionary parsed from the BGG API response.
    :return: The saved or updated Game object, or None if processing fails.
    """
    items_data = game_detail_data.get("items", {})
    # Single item requests return dict under 'item', multiple return list.
    game_item = items_data.get("item")

    # In single game fetch, get("item") could be a dict. In batch fetch, it might be a list
    # containing one dict if we are iterating. Ensure we handle both.
    if isinstance(game_item, list) and len(game_item) > 0:
        game_item = game_item[0]

    if not game_item:
        log.warning(f"No detail data found for BGG ID {bgg_id}")
        return None, None

    try:
        # Extract names (primary and alternative)
        names_data = game_item.get("name", [])
        if isinstance(names_data, dict):
            names_data = [names_data]

        primary_name_dict = next(
            (n for n in names_data if n.get("@type") == "primary"), None
        )
        if not primary_name_dict:
            # Fallback to the first available name if no primary is specified
            primary_name_dict = (
                names_data[0] if names_data else {"@value": "Unknown"}
            )

        game_name = primary_name_dict.get("@value")
        sub_name_list = [
            n.get("@value")
            for n in names_data
            if n.get("@type") == "alternate"
        ]
        sub_name = ", ".join(sub_name_list) if sub_name_list else None

        image_url = game_item.get("image")
        description = game_item.get("description")
        release_year_str = game_item.get("yearpublished", {}).get("@value")
        release_year = int(release_year_str) if release_year_str else None
        min_players_str = game_item.get("minplayers", {}).get("@value")
        min_players = int(min_players_str) if min_players_str else None
        max_players_str = game_item.get("maxplayers", {}).get("@value")
        max_players = int(max_players_str) if max_players_str else None
        min_play_time_str = game_item.get("minplaytime", {}).get("@value")
        min_play_time = int(min_play_time_str) if min_play_time_str else None
        max_play_time_str = game_item.get("maxplaytime", {}).get("@value")
        max_play_time = int(max_play_time_str) if max_play_time_str else None
        min_age_str = game_item.get("minage", {}).get("@value")
        min_age = int(min_age_str) if min_age_str else None

        # Statistics
        statistics = game_item.get("statistics", {}).get("ratings", {})

        bgg_rating_str = statistics.get("average", {}).get("@value")
        bgg_rating = float(bgg_rating_str) if bgg_rating_str else None

        complexity_str = statistics.get("averageweight", {}).get("@value")
        complexity = float(complexity_str) if complexity_str else None

        bgg_rank = None
        ranks = statistics.get("ranks", {}).get("rank", [])
        if isinstance(ranks, dict):
            ranks = [ranks]
        for rank_data in ranks:
            if rank_data.get("@name") == "boardgame":
                val = rank_data.get("@value")
                if val and val != "Not Ranked":
                    bgg_rank = int(val)
                break

        # We set image_path to None initially; caller manages image batch download.
        game_data: dict[str, Any] = {
            "name": game_name,
            "bgg_id": bgg_id,
            "sub_name": sub_name,
            "description": description,
            "release_year": release_year,
            "min_players": min_players,
            "max_players": max_players,
            "min_play_time": min_play_time,
            "max_play_time": max_play_time,
            "min_age": min_age,
            "image_path": None,
            "bgg_rating": bgg_rating,
            "bgg_rank": bgg_rank,
            "complexity": complexity,
        }

        # Check if game already exists
        statement = select(Game).where(Game.bgg_id == bgg_id)
        existing_game = session.exec(statement).first()

        if existing_game:
            # Update existing game details
            for key, value in game_data.items():
                # We don't overwrite image_path with None if we already have one
                if (
                    key == "image_path"
                    and existing_game.image_path is not None
                ):
                    continue
                setattr(existing_game, key, value)
            game_obj: Game = existing_game
        else:
            if "version" not in game_data:
                game_data["version"] = 0.0
            if game_data.get("description") is None:
                game_data["description"] = ""
            for field in [
                "release_year",
                "min_players",
                "max_players",
                "min_age",
                "min_play_time",
                "max_play_time",
            ]:
                if game_data.get(field) is None:
                    game_data[field] = 0
            if game_data.get("complexity") is None:
                game_data["complexity"] = 0.0

            game_obj = Game(id=uuid4().bytes, **game_data)
            session.add(game_obj)

        session.flush()  # Ensure game_obj gets an ID if it's new

        # --- Sub-entity Processing (Publishers, Persons, Categories, Related Games) ---
        links_data = game_item.get("link", [])
        if isinstance(links_data, dict):
            links_data = [links_data]

        publisher_data = [
            ld for ld in links_data if ld.get("@type") == "boardgamepublisher"
        ]
        person_role_map = {
            "boardgamedesigner": "author",
            "boardgameartist": "artist",
        }
        person_data = {
            role_bgg_type: [
                ld for ld in links_data if ld.get("@type") == role_bgg_type
            ]
            for role_bgg_type in person_role_map
        }
        category_data = [
            ld for ld in links_data if ld.get("@type") == "boardgamecategory"
        ]
        related_games_data = [
            ld
            for ld in links_data
            if ld.get("@type")
            in ("boardgameexpansion", "boardgamereimplementation")
        ]

        # Helper to get/create entity and link
        def get_or_create_entity_and_link(
            sess: SQLModelSession,
            model: type[
                Any
            ],  # Use Any to bypass strict type checker on dynamic ORM classes
            link_model: type[Any],
            entity_name_key: str,
            link_entity_id_attr: str,
            link_game_id_attr: str,
            bgg_data_list: list[dict[str, Any]],
            role_id: bytes | None = None,
        ) -> None:
            for item in bgg_data_list:
                entity_name = item.get("@value")

                statement_entity = select(model).where(
                    getattr(model, entity_name_key) == entity_name
                )
                entity = sess.exec(statement_entity).first()

                if not entity:
                    entity_kwargs = {
                        entity_name_key: entity_name,
                        "id": uuid4().bytes,
                    }
                    entity = model(**entity_kwargs)
                    sess.add(entity)
                    sess.flush()

                # Check if link exists
                statement_link = select(link_model).where(
                    getattr(link_model, link_entity_id_attr) == entity.id,
                    getattr(link_model, link_game_id_attr) == game_obj.id,
                )
                if role_id:
                    # Specific to PersonGameLink
                    statement_link = statement_link.where(
                        PersonGameLink.role_id == role_id
                    )

                existing_link = sess.exec(statement_link).first()

                if not existing_link:
                    link_kwargs: dict[str, Any] = {
                        link_entity_id_attr: entity.id,
                        link_game_id_attr: game_obj.id,
                    }
                    if role_id:
                        link_kwargs["role_id"] = role_id
                    new_link = link_model(**link_kwargs)
                    sess.add(new_link)
                    sess.flush()

        # 1. Publishers
        get_or_create_entity_and_link(
            session,
            Publisher,
            PublisherGameLink,
            "name",
            "publisher_id",
            "game_id",
            publisher_data,
        )

        # 2. Persons (Designers, Artists)
        for bgg_role_type, role_data in person_data.items():
            if role_data:
                role_name_db = person_role_map[bgg_role_type]
                statement_role = select(PersonRole).where(
                    PersonRole.role == role_name_db
                )
                role_obj = session.exec(statement_role).first()
                if not role_obj:
                    role_obj = PersonRole(id=uuid4().bytes, role=role_name_db)
                    session.add(role_obj)
                    session.flush()

                get_or_create_entity_and_link(
                    session,
                    Person,
                    PersonGameLink,
                    "name",
                    "person_id",
                    "game_id",
                    role_data,
                    role_obj.id,
                )

        # 3. Categories
        get_or_create_entity_and_link(
            session,
            Category,
            GameCategoryLink,
            "name",
            "category_id",
            "game_id",
            category_data,
        )

        # 4. Related Games
        for item in related_games_data:
            related_game_name = item.get("@value")
            related_bgg_id = int(item.get("@id", 0))
            relationship_type_name = item.get("@type")

            # Get relationship type
            statement_rel_type = select(GameRelationship).where(
                GameRelationship.type == relationship_type_name
            )
            rel_type = session.exec(statement_rel_type).first()
            if not rel_type:
                rel_type = GameRelationship(
                    id=uuid4().bytes, type=relationship_type_name
                )
                session.add(rel_type)
                session.flush()

            # We need the target game ID to make the relation. If it doesn't exist yet, we add a stub for now.
            target_stmt = select(Game).where(Game.bgg_id == related_bgg_id)
            target_game = session.exec(target_stmt).first()
            if not target_game:
                target_game = Game(
                    id=uuid4().bytes,
                    bgg_id=related_bgg_id,
                    name=related_game_name or "Unknown",
                    version=0.0,
                    description="",
                    release_year=0,
                    min_players=0,
                    max_players=0,
                    min_age=0,
                    min_play_time=0,
                    max_play_time=0,
                    complexity=0.0,
                    recommended_players=0,
                    bgg_rating=None,
                    bgg_rank=None,
                )
                session.add(target_game)
                session.flush()

            # Check if link exists
            statement_rg = select(RelatedGame).where(
                RelatedGame.source_game_id == game_obj.id,
                RelatedGame.target_game_id == target_game.id,
                RelatedGame.relationship_type_id == rel_type.id,
            )

            existing_rg = session.exec(statement_rg).first()

            if not existing_rg:
                rg_obj = RelatedGame(
                    source_game_id=game_obj.id,
                    target_game_id=target_game.id,
                    relationship_type_id=rel_type.id,
                )
                session.add(rg_obj)

        log.debug(
            f"Successfully processed and staged game: {game_name} (BGG ID: {bgg_id})"
        )
        session.refresh(game_obj)
        return game_obj, image_url

    except Exception as e:
        log.error(f"Error processing game {bgg_id}: {e}")
        return None, None


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
    :param get_versions: Whether to get detailed game version info or not.
    :type get_versions: bool
    :param get_videos: Whether to get detailed game video info or not.
    :type get_videos: bool
    :param get_comments: Whether to get detailed game comment info or not.
    :type get_comments: bool
    :param get_marketplacelistings: Whether to get detailed info on
        marketplace listings or not.
    :type get_marketplacelistings: bool
    :param get_trading: Whether to get detailed game trading info or not.
    :type get_trading: bool
    :param get_want: Whether to get detailed game want info or not.
    :type get_want: bool
    :param get_rank: Whether to get detailed game rank info or not.
    :type get_rank: bool
    :param get_image_list: Whether to get detailed game image info or not.
    :type get_image_list: bool
    :return: The detailed game info.
    :rtype: dict[str, Any]
    """
    if isinstance(game_ids, int):
        game_ids = [game_ids]

    # Generate the url (BGG API v2 'thing' endpoint for game details)
    url = f"{BGG_API_URL}thing"  # Base URL for thing (game/expansion)
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
