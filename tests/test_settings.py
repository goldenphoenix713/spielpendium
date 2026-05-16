from __future__ import annotations

from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine

from util.models import UserSettings
from util.settings import (
    get_active_username,
    get_all_usernames,
    get_setting,
    set_setting,
)


def test_settings_logic():
    # Use an in-memory database for this test
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Patch the engine used in util.settings
    with patch("util.settings.engine", engine):
        # Initial state (defaults)
        assert get_active_username() == ""
        assert get_all_usernames() == []

        # Set a simple setting
        set_setting("theme", "dark")
        assert get_setting("theme") == "dark"

        # Update a setting
        set_setting("theme", "light")
        assert get_setting("theme") == "light"

        # Set a complex setting (list)
        usernames = ["alice", "bob"]
        set_setting("bgg_usernames", usernames)
        assert get_setting("bgg_usernames") == usernames
        assert get_all_usernames() == usernames

        # Set a complex setting (dict)
        prefs = {"accent": "blue", "font": "Inter"}
        set_setting("prefs", prefs)
        assert get_setting("prefs") == prefs

        # Test default value
        assert get_setting("non_existent", "default_val") == "default_val"

        # Test JSON decode error (fallback to raw string)
        with Session(engine) as session:
            # Manually inject invalid JSON
            bad_setting = UserSettings(
                id=b"123", keyword="bad_json", value='{"missing_quote: 1}'
            )
            session.add(bad_setting)
            session.commit()

        assert get_setting("bad_json") == '{"missing_quote: 1}'
