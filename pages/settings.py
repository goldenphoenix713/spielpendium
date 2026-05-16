from __future__ import annotations

from typing import Any

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, html
from dash_iconify import DashIconify

from util.settings import (
    get_active_username,
    get_all_usernames,
    get_setting,
    set_setting,
)

dash.register_page(__name__, path="/settings")  # type: ignore[no-untyped-call]


def layout() -> dmc.Container:
    # Initial values for the components (will be updated by callback too)
    all_users = get_all_usernames()
    active_user = get_active_username()
    auto_refresh = get_setting("auto_refresh", False)
    page_size = get_setting("page_size", 50)
    theme = get_setting("theme", "dark")
    primary_color = get_setting("primary_color", "blue")

    # The data from get_setting can be a string, even though it should be a boolean.
    # This is because the data is stored as a string in the database.
    if isinstance(auto_refresh, str):
        auto_refresh = auto_refresh == "1" or auto_refresh.lower() == "true"

    return dmc.Container(
        size="md",
        pt="xl",
        children=[
            dmc.Group(
                [
                    dmc.Title("Settings", order=1),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Reset to Defaults",
                                id="settings-reset-btn",
                                variant="outline",
                                color="red",
                                size="sm",
                            ),
                            dmc.Button(
                                "Save Settings",
                                id="settings-save-btn",
                                leftSection=DashIconify(
                                    icon="tabler:device-floppy"
                                ),
                                size="sm",
                            ),
                        ],
                        gap="sm",
                    ),
                ],
                justify="space-between",
                align="center",
                mb="xl",
            ),
            dmc.Stack(
                gap="xl",
                children=[
                    # BGG Section
                    dmc.Card(
                        withBorder=True,
                        shadow="sm",
                        radius="md",
                        children=[
                            dmc.Group(
                                [
                                    DashIconify(
                                        icon="fa6-brands:font-awesome",
                                        width=20,
                                        color="var(--mantine-color-blue-6)",
                                    ),
                                    dmc.Text(
                                        "BoardGameGeek Integration",
                                        fw=700,
                                        size="lg",
                                    ),
                                ],
                                mb="md",
                            ),
                            dmc.Stack(
                                [
                                    dmc.TagsInput(
                                        id={
                                            "type": "setting",
                                            "item": "bgg_usernames",
                                        },
                                        label="Managed BGG Usernames",
                                        description="Add or remove usernames to track.",
                                        value=all_users,
                                        placeholder="Type and press enter...",
                                        clearable=True,
                                    ),
                                    dmc.Select(
                                        id="setting-active_bgg_username",
                                        label="Active Profile",
                                        description="The profile currently used to populate the collection.",
                                        data=[
                                            {"label": u, "value": u}
                                            for u in all_users
                                        ],
                                        value=active_user,
                                    ),
                                ],
                                gap="md",
                            ),
                        ],
                    ),
                    # Collection Section
                    dmc.Card(
                        withBorder=True,
                        shadow="sm",
                        radius="md",
                        children=[
                            dmc.Group(
                                [
                                    DashIconify(
                                        icon="tabler:settings",
                                        width=20,
                                        color="var(--mantine-color-teal-6)",
                                    ),
                                    dmc.Text(
                                        "Collection Preferences",
                                        fw=700,
                                        size="lg",
                                    ),
                                ],
                                mb="md",
                            ),
                            dmc.Stack(
                                [
                                    dmc.Group([
                                        dmc.Switch(
                                            id="setting-auto_refresh",
                                            label="Auto-refresh on load",
                                            description="Automatically check BGG for collection updates when opening the page.",
                                            checked=auto_refresh,
                                        ),
                                        # Proxy input removed, using string IDs directly
                                    ]),
                                    dmc.NumberInput(
                                        id="setting-page_size",
                                        label="Games per page",
                                        description="Number of games to render in the collection grid (10-200).",
                                        min=10,
                                        max=200,
                                        step=10,
                                        value=page_size,
                                    ),
                                ],
                                gap="md",
                            ),
                        ],
                    ),
                    # Appearance Section
                    dmc.Card(
                        withBorder=True,
                        shadow="sm",
                        radius="md",
                        children=[
                            dmc.Group(
                                [
                                    DashIconify(
                                        icon="tabler:palette",
                                        width=20,
                                        color="var(--mantine-color-grape-6)",
                                    ),
                                    dmc.Text(
                                        "Appearance",
                                        fw=700,
                                        size="lg",
                                    ),
                                ],
                                mb="md",
                            ),
                            dmc.Stack(
                                [
                                    dmc.Text(
                                        "Color Scheme", size="sm", fw=500
                                    ),
                                    dmc.SegmentedControl(
                                        id="setting-theme",
                                        value=theme,
                                        data=[
                                            {
                                                "label": dmc.Center([
                                                    DashIconify(
                                                        icon="tabler:sun",
                                                        width=16,
                                                    ),
                                                    dmc.Box("Light", ml=10),
                                                ]),
                                                "value": "light",
                                            },
                                            {
                                                "label": dmc.Center([
                                                    DashIconify(
                                                        icon="tabler:moon",
                                                        width=16,
                                                    ),
                                                    dmc.Box("Dark", ml=10),
                                                ]),
                                                "value": "dark",
                                            },
                                        ],
                                        fullWidth=True,
                                    ),
                                    dmc.Text(
                                        "Primary Color",
                                        size="sm",
                                        fw=500,
                                        mt="md",
                                    ),
                                    dmc.Select(
                                        id="setting-primary_color",
                                        value=primary_color,
                                        data=[
                                            {
                                                "label": c.capitalize(),
                                                "value": c,
                                            }
                                            for c in [
                                                "blue",
                                                "cyan",
                                                "grape",
                                                "green",
                                                "indigo",
                                                "lime",
                                                "orange",
                                                "pink",
                                                "red",
                                                "teal",
                                                "violet",
                                                "yellow",
                                            ]
                                        ],
                                        leftSection=dmc.Box(
                                            w=16,
                                            h=16,
                                            id="primary-color-swatch",
                                            style={
                                                "backgroundColor": f"var(--mantine-color-{primary_color}-filled)",
                                                "borderRadius": "50%",
                                            },
                                        ),
                                    ),
                                ],
                                gap="xs",
                            ),
                        ],
                    ),
                ],
            ),
            # Feedback notification
            html.Div(id="settings-notification-container"),
        ],
    )


@callback(
    Output("setting-active_bgg_username", "data"),
    Input({"type": "setting", "item": "bgg_usernames"}, "value"),
)
def update_active_dropdown_options(
    usernames: list[str],
) -> list[dict[str, str]]:
    """Update the 'Active Profile' dropdown options when the tags input changes."""
    return [{"label": u, "value": u} for u in usernames]


@callback(
    Output("setting-auto_refresh", "checked"),
    Input("setting-auto_refresh", "checked"),
    prevent_initial_call=True,
)
def sync_auto_refresh_value(checked: bool) -> bool:
    """Ensure auto-refresh setting in DB is synced when changed."""
    set_setting("auto_refresh", checked)
    return checked


@callback(
    Output("primary-color-swatch", "style"),
    Input("setting-primary_color", "value"),
)
def update_swatch_color(color: str) -> dict[str, str]:
    """Update the visual swatch in the dropdown when a new color is selected."""
    return {
        "backgroundColor": f"var(--mantine-color-{color}-filled)",
        "borderRadius": "50%",
    }


@callback(
    Output("settings-notification-container", "children"),
    Output("theme-store", "data", allow_duplicate=True),
    Output("primary-color-store", "data", allow_duplicate=True),
    Output("active-user-store", "data", allow_duplicate=True),
    Output("managed-users-store", "data", allow_duplicate=True),
    Input("settings-save-btn", "n_clicks"),
    State("setting-active_bgg_username", "value"),
    State({"type": "setting", "item": "bgg_usernames"}, "value"),
    State("setting-page_size", "value"),
    State("setting-theme", "value"),
    State("setting-primary_color", "value"),
    State("setting-auto_refresh", "checked"),
    prevent_initial_call=True,
)
def save_settings(
    n_clicks: int | None,
    username: str,
    usernames: list[str],
    page_size: int,
    theme: str,
    primary_color: str,
    auto_refresh: bool,
) -> (
    tuple[dmc.Notification, Any, Any, Any, Any]
    | tuple[
        dash.NoUpdate,
        dash.NoUpdate,
        dash.NoUpdate,
        dash.NoUpdate,
        dash.NoUpdate,
    ]
):
    """Save all settings to the database and show a notification."""
    if not n_clicks:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    try:
        # Align active username with the managed usernames list
        if not usernames:
            username = ""
        elif username not in usernames:
            username = usernames[0]

        set_setting("active_bgg_username", username)
        set_setting("bgg_usernames", usernames)
        set_setting("page_size", page_size)
        set_setting("theme", theme)
        set_setting("primary_color", primary_color)
        set_setting("auto_refresh", auto_refresh)

        return (
            dmc.Notification(
                title="Settings Saved",
                message="Your preferences have been updated successfully.",
                color="green",
                icon=DashIconify(icon="tabler:check"),
                action="show",
            ),
            theme,
            primary_color,
            username,
            usernames,
        )
    except Exception as e:
        return (
            dmc.Notification(
                title="Error Saving Settings",
                message=str(e),
                color="red",
                icon=DashIconify(icon="tabler:x"),
                action="show",
            ),
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )


@callback(
    Output("setting-active_bgg_username", "value"),
    Input("active-user-store", "data"),
)
def sync_active_user_from_store(active_user: str | None) -> str | None:
    """Initialize the Active Profile select from local storage."""
    return active_user


@callback(
    Output("setting-theme", "value"),
    Input("theme-store", "data"),
)
def sync_theme_from_store(theme: str | None) -> str | None:
    """Initialize the theme select from local storage."""
    return theme


@callback(
    Output("setting-primary_color", "value"),
    Input("primary-color-store", "data"),
)
def sync_primary_color_from_store(color: str | None) -> str | None:
    """Initialize the primary color select from local storage."""
    return color


@callback(
    Output({"type": "setting", "item": "bgg_usernames"}, "value"),
    Input("managed-users-store", "data"),
)
def sync_managed_users_from_store(usernames: list[str] | None) -> list[str]:
    """Initialize the managed usernames tags input from local storage."""
    return usernames or []


@callback(
    Output("setting-active_bgg_username", "value", allow_duplicate=True),
    Output(
        {"type": "setting", "item": "bgg_usernames"},
        "value",
        allow_duplicate=True,
    ),
    Output("setting-page_size", "value", allow_duplicate=True),
    Output("setting-theme", "value", allow_duplicate=True),
    Output("setting-primary_color", "value", allow_duplicate=True),
    Output("setting-auto_refresh", "checked", allow_duplicate=True),
    Output("theme-store", "data", allow_duplicate=True),
    Output("primary-color-store", "data", allow_duplicate=True),
    Output("active-user-store", "data", allow_duplicate=True),
    Output("managed-users-store", "data", allow_duplicate=True),
    Output(
        "settings-notification-container", "children", allow_duplicate=True
    ),
    Input("settings-reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_to_defaults(n_clicks: int | None) -> tuple[Any, ...]:
    if not n_clicks:
        return (dash.no_update,) * 11

    try:
        set_setting("active_bgg_username", "")
        set_setting("bgg_usernames", [])
        set_setting("page_size", 50)
        set_setting("theme", "dark")
        set_setting("primary_color", "blue")
        set_setting("auto_refresh", False)

        notification = dmc.Notification(
            title="Settings Reset",
            message="All settings have been reset to default values.",
            color="orange",
            icon=DashIconify(icon="tabler:rotate-clockwise"),
            action="show",
        )

        return (
            "",  # active_bgg_username
            [],  # bgg_usernames
            50,  # page_size
            "dark",  # theme
            "blue",  # primary_color
            False,  # auto_refresh
            "dark",  # theme-store
            "blue",  # primary-color-store
            "",  # active-user-store
            [],  # managed-users-store
            notification,  # notification
        )
    except Exception as e:
        notification = dmc.Notification(
            title="Error Resetting Settings",
            message=str(e),
            color="red",
            icon=DashIconify(icon="tabler:x"),
            action="show",
        )
        return (dash.no_update,) * 10 + (notification,)
