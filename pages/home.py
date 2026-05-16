from __future__ import annotations

from typing import TYPE_CHECKING, cast

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback
from dash_iconify import DashIconify

from util.settings import get_setting, set_setting

if TYPE_CHECKING:
    from dash import NoUpdate

dash.register_page(__name__, path="/")  # type: ignore[no-untyped-call]


def onboarding_ui() -> dmc.Container:
    return dmc.Container(
        size="sm",
        pt=80,
        children=[
            dmc.Stack(
                align="center",
                gap="xl",
                children=[
                    dmc.ThemeIcon(
                        DashIconify(icon="game-icons:meeple", width=60),
                        size=100,
                        radius=100,
                        variant="gradient",
                        gradient={"from": "blue", "to": "cyan", "deg": 45},
                    ),
                    dmc.Stack(
                        gap=0,
                        align="center",
                        children=[
                            dmc.Title(
                                "Welcome to Spielpendium", order=1, ta="center"
                            ),
                            dmc.Text(
                                "The premium companion for your BoardGameGeek collection.",
                                c="dimmed",
                                size="lg",
                                ta="center",
                            ),
                        ],
                    ),
                    dmc.Paper(
                        withBorder=True,
                        p="xl",
                        radius="md",
                        shadow="md",
                        w="100%",
                        children=[
                            dmc.Stack(
                                children=[
                                    dmc.TextInput(
                                        id="onboarding-username",
                                        label="BoardGameGeek Username",
                                        description="We'll use this to fetch your collection data.",
                                        placeholder="e.g. bgg_explorer",
                                        leftSection=DashIconify(
                                            icon="tabler:user"
                                        ),
                                        size="md",
                                    ),
                                    dmc.Button(
                                        "Connect Collection",
                                        id="onboarding-submit",
                                        fullWidth=True,
                                        size="md",
                                        variant="gradient",
                                        gradient={
                                            "from": "blue",
                                            "to": "cyan",
                                        },
                                        leftSection=DashIconify(
                                            icon="tabler:plug-connected"
                                        ),
                                    ),
                                ]
                            )
                        ],
                    ),
                    dmc.SimpleGrid(
                        cols=2,
                        spacing="xl",
                        mt="xl",
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:cards"),
                                        variant="light",
                                        radius="md",
                                    ),
                                    dmc.Text(
                                        "Beautiful Card UI", size="sm", fw=500
                                    ),
                                ]
                            ),
                            dmc.Group(
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:chart-bar"),
                                        variant="light",
                                        radius="md",
                                    ),
                                    dmc.Text(
                                        "Advanced Stats", size="sm", fw=500
                                    ),
                                ]
                            ),
                            dmc.Group(
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:filter"),
                                        variant="light",
                                        radius="md",
                                    ),
                                    dmc.Text(
                                        "Powerful Filters", size="sm", fw=500
                                    ),
                                ]
                            ),
                            dmc.Group(
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:refresh"),
                                        variant="light",
                                        radius="md",
                                    ),
                                    dmc.Text(
                                        "Instant BGG Sync", size="sm", fw=500
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            )
        ],
    )


def home_ui(username: str) -> dmc.Container:
    return dmc.Container(
        size="md",
        pt=100,
        children=[
            dmc.Stack(
                align="center",
                gap="xl",
                children=[
                    dmc.Title(f"Welcome Back, {username}", order=1),
                    dmc.Text(
                        "Your collection is ready for browsing.",
                        c="dimmed",
                        size="lg",
                    ),
                    dmc.Group(
                        children=[
                            dmc.Anchor(
                                dmc.Button(
                                    "Browse Collection",
                                    size="lg",
                                    leftSection=DashIconify(
                                        icon="game-icons:card-draw"
                                    ),
                                ),
                                href="/collection",
                                underline="never",
                            ),
                            dmc.Anchor(
                                dmc.Button(
                                    "View Insights",
                                    variant="outline",
                                    size="lg",
                                    leftSection=DashIconify(
                                        icon="game-icons:histogram"
                                    ),
                                ),
                                href="/statistics",
                                underline="never",
                            ),
                        ]
                    ),
                ],
            )
        ],
    )


def layout() -> dmc.Container:
    return dmc.Container(id="home-page-container", fluid=True)


@callback(
    Output("home-page-container", "children"),
    Input("active-user-store", "data"),
)
def render_home_content(active_user: str | None) -> dmc.Container:
    """Render either onboarding or welcome back UI based on local storage."""
    if not active_user:
        return onboarding_ui()
    return home_ui(active_user)


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("active-user-store", "data"),
    Output("managed-users-store", "data", allow_duplicate=True),
    Input("onboarding-submit", "n_clicks"),
    State("onboarding-username", "value"),
    prevent_initial_call=True,
)
def handle_onboarding(
    n_clicks: int | None, username: str | None
) -> tuple[str, str, list[str]] | NoUpdate:
    if not n_clicks or not username:
        return dash.no_update

    # Clean the username
    username = username.strip()
    if not username:
        return dash.no_update

    # Save to database (as a fallback/record)
    set_setting("active_bgg_username", username)

    # Update bgg_usernames list if not already there
    existing_usernames = cast("list[str]", get_setting("bgg_usernames", []))
    if username not in existing_usernames:
        existing_usernames.append(username)
        set_setting("bgg_usernames", existing_usernames)

    # Redirect to collection and update local store
    return "/collection", username, existing_usernames
