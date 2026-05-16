from __future__ import annotations

import json
from typing import Any, cast

from sqlmodel import Session, select

from util.models import UserSettings, engine


def get_setting(keyword: str, default: Any = None) -> Any:
    """
    Retrieve a setting from the database.
    If the value is JSON-serializable (starts with [ or {), it attempts to decode it.
    """
    with Session(engine) as session:
        statement = select(UserSettings).where(UserSettings.keyword == keyword)
        setting = session.exec(statement).first()

        if not setting:
            return default

        val = setting.value
        # Basic JSON detection
        if val.startswith(("[", "{", '"')):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return val


def set_setting(keyword: str, value: Any) -> None:
    """
    Save or update a setting in the database.
    Complex types (list, dict) are automatically JSON-serialized.
    """
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
            setting.value = str_val
        else:
            from uuid import uuid4

            setting = UserSettings(
                id=uuid4().bytes, keyword=keyword, value=str_val
            )
            session.add(setting)

        session.commit()


def get_active_username() -> str:
    """Helper to get the current active BGG username."""
    val = get_setting("active_bgg_username", "")
    if not val or val == "None":
        return ""
    return cast("str", val)


def get_all_usernames() -> list[str]:
    """Helper to get the list of all configured BGG usernames."""
    return cast("list[str]", get_setting("bgg_usernames", []))
