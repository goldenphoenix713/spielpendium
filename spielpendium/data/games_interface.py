""" The Spielpendium side of the Spielpendium-BGG interface."""

__all__ = ['import_user_data']

from typing import Dict, List, Optional, Union
from operator import itemgetter

from spielpendium.network import get_user_game_collection, get_game_info,\
    get_images


def get_name(ii_game: Dict) -> str:
    if isinstance(ii_game['name'], dict):
        return ii_game['name']['#text']

    if isinstance(ii_game['name'], list):
        return [name['#text'] for name in ii_game['name']
                if '@primary' in name.keys()][0]

    return ''


def get_authors(ii_game: Dict) -> str:
    try:
        if isinstance(ii_game['boardgamedesigner'], dict):
            return ii_game['boardgamedesigner']['#text']

        if isinstance(ii_game['boardgamedesigner'], list):
            return ', '.join([author['#text'] for author
                              in ii_game['boardgamedesigner']])
    except KeyError:
        return 'No Authors Listed'
    return ''


def get_artists(ii_game: Dict) -> str:
    try:
        if isinstance(ii_game['boardgameartist'], dict):
            return ii_game['boardgameartist']['#text']

        if isinstance(ii_game['boardgameartist'], list):
            return ', '.join([artist['#text'] for artist
                              in ii_game['boardgameartist']])
    except KeyError:
        return 'No Artists Listed'

    return ''


def get_categories(ii_game: Dict) -> str:
    if isinstance(ii_game['boardgamecategory'], dict):
        return ii_game['boardgamecategory']['#text']

    if isinstance(ii_game['boardgamecategory'], list):
        return ', '.join([category['#text'] for category
                          in ii_game['boardgamecategory']])

    return ''


def get_recommended_players(ii_game: Dict) -> str:
    """ Reads the user poll in the BGG data and returns the highest
    recommended number of players for the game

    :param ii_game: The iith game in the game list
    :return: The recommended number of players.
    """
    polls = ii_game['poll']
    num_player_poll = [poll['results'] for poll in polls
                       if poll['@name'] == 'suggested_numplayers'][0]

    if isinstance(num_player_poll, list):
        best_votes = [(results['@numplayers'],
                       [int(num_votes['@numvotes'])
                        for num_votes in results['result']
                        if num_votes['@value'] == 'Best'][0])
                      for results in num_player_poll]
        return max(best_votes, key=itemgetter(1))[0]
    elif isinstance(num_player_poll, dict):
        return num_player_poll['@numplayers']


def get_bgg_rank(ii_game: Dict) -> str:
    """ Finds the general BGG rank for the game and returns it.

    :param ii_game: The iith game in the game list.
    :return: The BGG rank for the game.
    """
    ranks = ii_game['statistics']['ratings']['ranks']['rank']
    rank = ''

    if isinstance(ranks, list):
        rank = [rank['@value'] for rank in ranks
                if rank['@name'] == 'boardgame'][0]
    elif isinstance(ranks, dict):
        rank = ranks['@value']

    return rank


def get_related_games(ii_game: Dict):
    ii_game.keys()
    pass


def import_user_data(username: str,
                     filters: Optional[Dict[str, Union[int, bool]]] = None,
                     **kwargs
                     ) -> List[Dict]:
    """ Takes information downloaded using the BGG APT and conditions it to
    the format needed by a Games object.

    :param username: The BGG username who's collection we're importing.
    :param filters: Additional filters for the game collection.
    :return: A dict in the format needed by a Games object.
    """

    user_collection = get_user_game_collection(username, filters, **kwargs)

    num_items = int(user_collection['items']['@totalitems'])

    game_ids = [user_collection['items']['item'][ii]['@objectid']
                for ii in range(num_items)]

    game_info = get_game_info(game_ids, stats=True)

    boardgame_list = game_info['boardgames']['boardgame']

    image_urls = [boardgame_list[ii]['image'] for ii in range(num_items)]

    images = get_images(image_urls)

    data = []

    for ii, game in enumerate(boardgame_list):
        data.append(
            {
                'BGG Id': game['@objectid'],
                'Image': images[ii],
                'Name': get_name(game),
                # TODO This will need user input to choose?
                'Version': game['boardgameversion'],
                'Author': get_authors(game),
                'Artist': get_artists(game),
                # TODO This will (surprisingly?) need user input to choose?
                'Publisher': game['boardgamepublisher'],
                'Release Year': game['yearpublished'],
                'Category': get_categories(game),
                'Description': game['description'],
                'Minimum Players': game['minplayers'],
                'Maximum Players': game['maxplayers'],
                'Recommended Players': get_recommended_players(game),
                'Age': game['age'],
                'Minimum Play Time': game['minplaytime'],
                'Maximum Play Time': game['maxplaytime'],
                'BGG Rating': game['statistics']['ratings']['average'],
                'BGG Rank': get_bgg_rank(game),
                'Complexity': game['statistics']['ratings']['averageweight'],
                'Related Games': get_related_games(game),
            }
        )

    return data


if __name__ == '__main__':
    import_user_data('phoenix713')
