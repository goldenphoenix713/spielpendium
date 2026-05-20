from __future__ import annotations

from typing import Any, cast

from loguru import logger as log

from util.models import engine  # noqa: F401

# In-memory settings store for backwards compatibility and test defaults
_IN_MEMORY_SETTINGS: dict[str, Any] = {}


def get_setting(keyword: str, default: Any = None) -> Any:
    """
    Retrieve a setting from the in-memory store.
    """
    log.debug(
        f"Retrieving setting for keyword: '{keyword}' (default: {default})"
    )
    val = _IN_MEMORY_SETTINGS.get(keyword, default)
    log.debug(f"Retrieved setting for '{keyword}': '{val}'")
    return val


def set_setting(keyword: str, value: Any) -> None:
    """
    Save or update a setting in the in-memory store.
    """
    log.info(f"Saving/updating setting: '{keyword}' = {value}")
    _IN_MEMORY_SETTINGS[keyword] = value


def get_active_username() -> str:
    """Helper to get the current active BGG username."""
    val = get_setting("active_bgg_username", "")
    if not val or val == "None":
        return ""
    return cast("str", val)


def get_all_usernames() -> list[str]:
    """Helper to get the list of all configured BGG usernames."""
    return cast("list[str]", get_setting("bgg_usernames", []))
