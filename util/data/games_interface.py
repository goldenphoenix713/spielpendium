"""The Spielpendium side of the Spielpendium-BGG interface."""

from operator import itemgetter
from typing import Any

from api import (
    get_game_info,
    get_images,
    get_user_game_collection,
)

__author__ = "Eduardo Ruiz"

__all__ = ["import_user_data"]

GAME_TYPE = dict[str, Any]


def get_name(game: GAME_TYPE) -> str | list[str]:
    if isinstance(game["name"], dict):
        return game["name"]["#text"]
    else:
        if any("@primary" in name for name in game["name"]):
            return [
                name["#text"] for name in game["name"] if "@primary" in name
            ][0]
        else:
            return [name["#text"] for name in game["name"]]


def get_authors(
    game: dict[str, dict[str, str] | list[dict[str, str]]],
) -> str:
    try:
        if isinstance(game["boardgamedesigner"], dict):
            return game["boardgamedesigner"]["#text"]
        else:
            return ", ".join([
                author["#text"] for author in game["boardgamedesigner"]
            ])
    except KeyError:
        return "No Authors Listed"


def get_artists(game: GAME_TYPE) -> str:
    try:
        if isinstance(game["boardgameartist"], dict):
            return game["boardgameartist"]["#text"]
        else:
            return ", ".join([
                artist["#text"] for artist in game["boardgameartist"]
            ])
    except KeyError:
        return "No Artists Listed"


def get_categories(game: GAME_TYPE) -> str:
    if isinstance(game["boardgamecategory"], dict):
        return game["boardgamecategory"]["#text"]
    else:
        return ", ".join([
            category["#text"] for category in game["boardgamecategory"]
        ])


def get_recommended_players(game: GAME_TYPE) -> str:
    """Reads the user poll in the BGG data and returns the highest
    recommended number of players for the game

    :param game: The iith game in the game list
    :return: The recommended number of players.
    """
    polls = game["poll"]  # pyright: ignore[reportAssignmentType]
    num_player_poll = [
        poll["results"]
        for poll in polls
        if poll["@name"] == "suggested_numplayers"
    ][0]

    if isinstance(num_player_poll, list):
        best_votes = [
            (
                results["@numplayers"],
                [
                    int(num_votes["@numvotes"])
                    for num_votes in results["result"]
                    if num_votes["@value"] == "Best"
                ][0],
            )
            for results in num_player_poll
        ]
        players: str = max(best_votes, key=itemgetter(1))[0]
    elif isinstance(num_player_poll, dict):
        players: str = num_player_poll["@numplayers"]
    else:
        raise TypeError("Unknown type of poll")

    return players


def get_bgg_rank(game: dict) -> str:
    """Finds the general BGG rank for the game and returns it.

    :param game: The iith game in the game list.
    :return: The BGG rank for the game.
    """
    ranks = game["statistics"]["ratings"]["ranks"]["rank"]
    rank = ""

    if isinstance(ranks, list):
        rank = [
            rank["@value"] for rank in ranks if rank["@name"] == "boardgame"
        ][0]
    elif isinstance(ranks, dict):
        rank = ranks["@value"]

    return rank


def get_version(game: dict) -> dict:
    """Finds the game version(s) for the game and returns them.

    :param game: The iith game in the game list.
    :return: The version(s) of the game.
    """
    return dict_list_to_dict(game["boardgameversion"])


def get_publisher(game: dict) -> dict:
    """Finds the game publisher(s) for the game and returns them.

    :param game: The iith game in the game list.
    :return: The publisher(s) of the game.
    """
    return dict_list_to_dict(game["boardgamepublisher"])


def get_related_games(game: dict) -> dict:
    """Finds the related game(s) for the game and returns them.

    :param game: The iith game in the game list.
    :return: The related game(s) of the game.
    """
    keys_to_look_for = ("boardgameexpansion", "boardgmeaccessory")
    related_games = {}
    for key in keys_to_look_for:
        if key in game:
            related_games.update(dict_list_to_dict(game[key]))

    return related_games


def dict_list_to_dict(dict_list: dict | list[dict]) -> dict:  # type:ignore
    """Finds the game version(s) for the game and returns them.

    :param dict_list: A dict or list of dicts with objectid and text keys
    :return: The converted data
    """
    publishers = {}
    items = []

    if isinstance(dict_list, dict):
        items = [dict_list]
    elif isinstance(dict_list, list):
        items = dict_list

    publishers.update({item["@objectid"]: item["#text"] for item in items})

    return publishers


def import_user_data(
    username: str,
    force_update: bool = False,
    filters: dict[str, int | bool] | None = None,  # type:ignore
) -> list[dict[str, str]]:
    """Takes information downloaded using the BGG API and conditions it to
    the format needed by a Games object.

    :param username: The BGG username whose collection we're importing.
    :param filters: Additional filters for the game collection.
    :param force_update: Whether to force an update from the API.
    :return: A dict in the format needed by a Games object.
    """

    user_collection = get_user_game_collection(username, filters, force_update)

    num_items = int(user_collection["items"]["@totalitems"])

    game_ids = [
        user_collection["items"]["item"][ii]["@objectid"]
        for ii in range(num_items)
    ]

    game_info = get_game_info(game_ids, get_stats=True)

    boardgame_list = game_info["boardgames"]["boardgame"]

    image_urls = [boardgame_list[ii]["image"] for ii in range(num_items)]

    images = get_images(image_urls)

    data = []

    for ii, game in enumerate(boardgame_list):
        data.append({
            "BGG Id": game["@objectid"],
            "Image": images[ii],
            "Name": get_name(game),
            "Version": get_version(game),
            "Author": get_authors(game),
            "Artist": get_artists(game),
            "Publisher": game["boardgamepublisher"],
            "Release Year": game["yearpublished"],
            "Category": get_categories(game),
            "Description": game["description"],
            "Minimum Players": game["minplayers"],
            "Maximum Players": game["maxplayers"],
            "Recommended Players": get_recommended_players(game),
            "Age": game["age"],
            "Minimum Play Time": game["minplaytime"],
            "Maximum Play Time": game["maxplaytime"],
            "BGG Rating": game["statistics"]["ratings"]["average"],
            "BGG Rank": get_bgg_rank(game),
            "Complexity": game["statistics"]["ratings"]["averageweight"],
            "Related Games": get_related_games(game),
        })

    return data


if __name__ == "__main__":
    ...
    # from pprint import pprint
    # from spielpendium.constants import DB_FILE

    # ans2 = user_exists('pizza')
    # print(ans2)

    # user_data = import_user_data('phoenix713')
    # pprint(user_data, indent=2)
