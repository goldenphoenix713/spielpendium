from __future__ import annotations

from unittest.mock import MagicMock

import dash

dash.register_page = MagicMock()  # type: ignore[invalid-assignment]  # ty:ignore[invalid-assignment]

from util.settings import (  # noqa: E402
    get_active_username,
    get_all_usernames,
    get_setting,
    set_setting,
)


def test_settings_logic():
    # Reset internal settings for test run purity
    from util.settings import _IN_MEMORY_SETTINGS

    _IN_MEMORY_SETTINGS.clear()

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
