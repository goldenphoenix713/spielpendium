from __future__ import annotations

from unittest.mock import patch

import dash_mantine_components as dmc

from pages.home import layout as home_layout
from pages.settings import layout as settings_layout
from pages.settings import (
    save_settings,
    sync_auto_refresh_value,
    update_active_dropdown_options,
    update_swatch_color,
)


def test_home_layout():
    layout = home_layout
    assert isinstance(layout, dmc.Container)
    # Check for welcome text
    assert "Welcome to Spielpendium" in str(layout)


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
    assert sync_auto_refresh_value(True) == 1
    assert sync_auto_refresh_value(False) == 0
    assert sync_auto_refresh_value(None) == 1

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

        assert save_settings(None, ["dark", "blue"]) == (
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

        # n_clicks is 1
        res = save_settings(1, ["dark", "blue"])
        assert isinstance(res[0], dmc.Notification)
        assert res[1] == "dark"
        assert res[2] == "blue"
        assert mock_set.call_count == 2
