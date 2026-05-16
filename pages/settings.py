from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dash import NoUpdate

import dash
import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html
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
            dmc.Title("Settings", order=1, mb="xl"),
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
                                        id={
                                            "type": "setting",
                                            "item": "active_bgg_username",
                                        },
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
                                            id={
                                                "type": "hidden_setting",
                                                "item": "auto_refresh",
                                            },
                                            label="Auto-refresh on load",
                                            description="Automatically check BGG for collection updates when opening the page.",
                                            checked=auto_refresh,
                                        ),
                                        # Hidden input to act as a proxy for the switch value so we can use ALL pattern matching
                                        dcc.Input(
                                            id={
                                                "type": "setting",
                                                "item": "auto_refresh",
                                            },
                                            value=int(auto_refresh),
                                            type="hidden",
                                        ),
                                    ]),
                                    dmc.NumberInput(
                                        id={
                                            "type": "setting",
                                            "item": "page_size",
                                        },
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
                                        id={
                                            "type": "setting",
                                            "item": "theme",
                                        },
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
                                        id={
                                            "type": "setting",
                                            "item": "primary_color",
                                        },
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
                    # Actions
                    dmc.Group(
                        [
                            dmc.Button(
                                "Save Settings",
                                id="settings-save-btn",
                                leftSection=DashIconify(
                                    icon="tabler:device-floppy"
                                ),
                                size="md",
                            ),
                            dmc.Button(
                                "Reset to Defaults",
                                id="settings-reset-btn",
                                variant="outline",
                                color="red",
                                size="md",
                            ),
                        ],
                        justify="flex-end",
                        mt="xl",
                    ),
                ],
            ),
            # Feedback notification
            html.Div(id="settings-notification-container"),
        ],
    )


@callback(
    Output({"type": "setting", "item": "active_bgg_username"}, "data"),
    Input({"type": "setting", "item": "bgg_usernames"}, "value"),
)
def update_active_dropdown_options(
    usernames: list[str],
) -> list[dict[str, str]]:
    """Update the 'Active Profile' dropdown options when the tags input changes."""
    return [{"label": u, "value": u} for u in usernames]


@callback(
    Output({"type": "setting", "item": MATCH}, "value"),
    Input({"type": "hidden_setting", "item": MATCH}, "checked"),
)
def sync_auto_refresh_value(checked: bool | None) -> int:
    """Sync the switch state to the hidden input for pattern matching."""
    if checked is None:
        return 1
    return int(checked)


@callback(
    Output("primary-color-swatch", "style"),
    Input({"type": "setting", "item": "primary_color"}, "value"),
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
    Input("settings-save-btn", "n_clicks"),
    State({"type": "setting", "item": ALL}, "value"),
    prevent_initial_call=True,
)
def save_settings(
    n_clicks: int | None,
    values: list[Any],
) -> (
    tuple[dmc.Notification, Any, Any, Any]
    | tuple[dash.NoUpdate, dash.NoUpdate, dash.NoUpdate, dash.NoUpdate]
):
    """Save all settings to the database and show a notification."""
    if not n_clicks:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    settings_map: dict[str, Any] = {}

    for i, state in enumerate(dash.ctx.states_list[0]):
        item = state["id"]["item"]
        val = values[i]

        if item == "auto_refresh":
            val = bool(int(val))

        if val is not None:
            settings_map[item] = val

    try:
        # Save each setting found in the map
        for key, val in settings_map.items():
            set_setting(key, val)

        return (
            dmc.Notification(
                title="Settings Saved",
                message="Your preferences have been updated successfully.",
                color="green",
                icon=DashIconify(icon="tabler:check"),
                action="show",
            ),
            settings_map.get("theme", dash.no_update),
            settings_map.get("primary_color", dash.no_update),
            settings_map.get("active_bgg_username", dash.no_update),
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
        )


@callback(
    Output({"type": "setting", "item": "active_bgg_username"}, "value"),
    Input("active-user-store", "data"),
    prevent_initial_call=True,
)
def sync_active_user_from_store(active_user: str | None) -> str | NoUpdate:
    """Initialize the Active Profile select from local storage."""
    if not active_user:
        return dash.no_update
    return active_user
