from __future__ import annotations

import json
from typing import Any, cast

from loguru import logger as log
from sqlmodel import Session, select

from util.models import UserSettings, engine


def get_setting(keyword: str, default: Any = None) -> Any:
    """
    Retrieve a setting from the database.
    If the value is JSON-serializable (starts with [ or {), it attempts to decode it.
    """
    log.debug(
        f"Retrieving setting for keyword: '{keyword}' (default: {default})"
    )
    with Session(engine) as session:
        statement = select(UserSettings).where(UserSettings.keyword == keyword)
        setting = session.exec(statement).first()

        if not setting:
            log.debug(
                f"Setting for '{keyword}' not found in database. Returning default: {default}"
            )
            return default

        val = setting.value
        # Basic JSON detection
        if val.startswith(("[", "{", '"')):
            try:
                decoded = json.loads(val)
                log.debug(f"Decoded JSON setting for '{keyword}': {decoded}")
                return decoded
            except json.JSONDecodeError as e:
                log.warning(
                    f"Failed to decode JSON setting for '{keyword}' with value: '{val}'. Error: {e}. Returning raw string."
                )
                return val
        log.debug(f"Retrieved raw setting for '{keyword}': '{val}'")
        return val


def set_setting(keyword: str, value: Any) -> None:
    """
    Save or update a setting in the database.
    Complex types (list, dict) are automatically JSON-serialized.
    """
    log.info(f"Saving/updating setting: '{keyword}' = {value}")
    if value is None:
        str_val = ""
    elif isinstance(value, (list, dict)):
        str_val = json.dumps(value)
    else:
        str_val = str(value)

    with Session(engine) as session:
        statement = select(UserSettings).where(UserSettings.keyword == keyword)
        setting = session.exec(statement).first()

        if setting:
            log.debug(
                f"Updating existing setting '{keyword}' from '{setting.value}' to '{str_val}'"
            )
            setting.value = str_val
        else:
            from uuid import uuid4

            log.debug(
                f"Creating new setting '{keyword}' with value '{str_val}'"
            )
            setting = UserSettings(
                id=uuid4().bytes, keyword=keyword, value=str_val
            )
            session.add(setting)

        session.commit()
        log.debug(f"Setting '{keyword}' successfully committed to DB.")


def get_active_username() -> str:
    """Helper to get the current active BGG username."""
    val = get_setting("active_bgg_username", "")
    if not val or val == "None":
        return ""
    return cast("str", val)


def get_all_usernames() -> list[str]:
    """Helper to get the list of all configured BGG usernames."""
    return cast("list[str]", get_setting("bgg_usernames", []))
