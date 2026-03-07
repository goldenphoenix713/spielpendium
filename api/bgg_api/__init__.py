"""The BGG API side of the Spielpendium-BGG interface."""

from .client import get_xml_info, search_bgg
from .collection import get_user_game_collection, user_exists_in_db
from .game_details import get_game_info
from .images import get_images

__all__ = [
    "search_bgg",
    "get_user_game_collection",
    "get_game_info",
    "get_images",
    "get_xml_info",
    "user_exists_in_db",
]
