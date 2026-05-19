from __future__ import annotations

from unittest.mock import patch

import dash_mantine_components as dmc

with patch("dash.register_page"):
    from pages.home import layout as home_layout
    from pages.settings import layout as settings_layout
from pages.settings import (
    reset_to_defaults,
    save_settings,
    sync_auto_refresh_value,
    update_active_dropdown_options,
    update_swatch_color,
)


def test_home_layout():
    from pages.home import render_home_content

    layout = home_layout()
    assert getattr(layout, "id", None) == "home-page-container"

    # Test onboarding content
    content = render_home_content(None)
    assert "Welcome to Spielpendium" in str(content)
    assert "Connect Collection" in str(content)

    # Test welcome back content
    content = render_home_content("testuser")
    assert "Welcome Back, testuser" in str(content)


def test_settings_layout():
    # Mock settings calls
    with (
        patch("pages.settings.get_all_usernames", return_value=["testuser"]),
        patch("pages.settings.get_active_username", return_value="testuser"),
        patch("pages.settings.get_setting", side_effect=lambda k, d: d),
    ):
        layout = settings_layout()
        assert isinstance(layout, dmc.Container)
        assert "Settings" in str(layout)
        assert "testuser" in str(layout)


def test_settings_callbacks():
    # update_active_dropdown_options
    assert update_active_dropdown_options(["a", "b"]) == [
        {"label": "a", "value": "a"},
        {"label": "b", "value": "b"},
    ]

    # sync_auto_refresh_value
    assert sync_auto_refresh_value(True) is True
    assert sync_auto_refresh_value(False) is False

    # update_swatch_color
    style = update_swatch_color("red")
    assert "red" in style["backgroundColor"]


def test_save_settings_callback():
    # Mock dash context and set_setting
    with (
        patch("pages.settings.dash.ctx") as mock_ctx,
        patch("pages.settings.set_setting") as mock_set,
    ):
        mock_ctx.states_list = [
            [{"id": {"item": "theme"}}, {"id": {"item": "primary_color"}}]
        ]

        # n_clicks is None
        import dash

        assert save_settings(
            None, "user", ["user"], 50, "dark", "blue", True
        ) == (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

        # n_clicks is 1
        res = save_settings(
            1, "user", ["user"], 50, "dark", "blue", True, "list"
        )
        assert isinstance(res[0], dmc.Notification)
        assert res[1] == "dark"
        assert res[2] == "blue"
        assert res[3] == "user"
        assert res[4] == ["user"]
        assert res[5] == "list"
        assert mock_set.call_count == 7

        # Test empty usernames list alignment
        res_empty = save_settings(1, "user", [], 50, "dark", "blue", True)
        assert res_empty[3] == ""
        assert res_empty[4] == []
        assert res_empty[5] == "grid"

        # Test active user fallback alignment
        res_fallback = save_settings(
            1, "other_user", ["user1", "user2"], 50, "dark", "blue", True
        )
        assert res_fallback[3] == "user1"
        assert res_fallback[4] == ["user1", "user2"]
        assert res_fallback[5] == "grid"


def test_reset_settings_callback():
    # Mock set_setting
    with patch("pages.settings.set_setting") as mock_set:
        import dash

        # n_clicks is None
        assert reset_to_defaults(None) == (dash.no_update,) * 13

        # n_clicks is 1
        res = reset_to_defaults(1)
        assert res[0] == ""
        assert res[1] == []
        assert res[2] == 50
        assert res[3] == "dark"
        assert res[4] == "blue"
        assert res[5] is False
        assert res[6] == "grid"
        assert res[7] == "dark"
        assert res[8] == "blue"
        assert res[9] == ""
        assert res[10] == []
        assert res[11] == "grid"
        assert isinstance(res[12], dmc.Notification)
        assert mock_set.call_count == 7


def test_handle_onboarding_callback():
    import dash

    from pages.home import handle_onboarding

    # n_clicks is None
    assert handle_onboarding(None, "user") == dash.no_update
    assert handle_onboarding(1, "") == dash.no_update

    with patch("pages.home.set_setting") as mock_set:
        res = handle_onboarding(1, "new_user")
        assert res[0] == "/collection"
        assert res[1] == "new_user"
        assert "new_user" in res[2]
        assert mock_set.call_count == 2
