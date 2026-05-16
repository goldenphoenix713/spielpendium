from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc

# noinspection PyProtectedMember
from dash import (
    Dash,
    Input,
    Output,
    State,
    _dash_renderer,
    callback,
    dcc,
    page_container,
)
from dash_iconify import DashIconify

import util.filters  # noqa: F401 — registers filter callbacks
from util.filters import generate_drawer_content, generate_sidebar
from util.models import create_db_and_tables
from util.settings import get_setting

# noinspection PyProtectedMember
_dash_renderer._set_react_version("18.2.0")  # type: ignore  # ty: ignore[unused-type-ignore-comment, unused-ignore-comment]


def generate_app() -> Dash:
    # Ensure database and tables exist on startup
    create_db_and_tables()

    app = Dash(__name__, use_pages=True)

    # Header content
    header_content = dmc.Group(
        justify="space-between",
        h="100%",
        px="md",
        children=[
            dmc.Group([
                dmc.ActionIcon(
                    DashIconify(icon="tabler:menu-2", width=20),
                    id="burger-button",
                    variant="subtle",
                    size="lg",
                    hiddenFrom="sm",
                ),
                DashIconify(icon="game-icons:meeple", width=30),
                dmc.Title("Spielpendium", order=3),
                dmc.Group(
                    gap="xs",
                    p="md",
                    visibleFrom="sm",
                    children=[
                        dmc.Anchor(
                            dmc.Button(
                                "Collection",
                                leftSection=DashIconify(
                                    icon="game-icons:card-draw", width=16
                                ),
                                variant="subtle",
                            ),
                            href="/collection",
                            underline="never",
                        ),
                        dmc.Button(
                            "Statistics",
                            leftSection=DashIconify(
                                icon="game-icons:histogram", width=16
                            ),
                            variant="subtle",
                            disabled=True,
                        ),
                        dmc.Anchor(
                            dmc.Button(
                                "Settings",
                                leftSection=DashIconify(
                                    icon="game-icons:gears", width=16
                                ),
                                variant="subtle",
                            ),
                            href="/settings",
                            underline="never",
                        ),
                    ],
                ),
            ]),
            dmc.Anchor(
                dmc.ActionIcon(
                    DashIconify(icon="radix-icons:github-logo", width=20),
                    variant="subtle",
                    color="gray",
                    size="lg",
                ),
                href="https://github.com/goldenphoenix713/spielpendium",
                target="_blank",
            ),
        ],
    )

    # Navbar content: filters sidebar
    navbar_content = dmc.ScrollArea(
        h="100%",
        type="scroll",
        children=generate_sidebar(),
    )

    # Mobile filter drawer
    mobile_drawer = dmc.Drawer(
        id="mobile-filter-drawer",
        title="Filters & Sort",
        opened=False,
        position="left",
        size="300px",
        padding="md",
        children=dmc.ScrollArea(
            h="100%",
            type="scroll",
            children=dmc.Stack(
                gap="lg",
                children=generate_drawer_content(),
            ),
        ),
    )

    app.layout = dmc.MantineProvider(
        id="mantine-provider",
        forceColorScheme=get_setting("theme", "dark"),
        theme={"primaryColor": get_setting("primary_color", "blue")},
        children=[
            mobile_drawer,
            dcc.Location(id="url"),
            dmc.AppShell(
                id="app-shell",
                children=[
                    dmc.AppShellHeader(
                        header_content,
                        px="md",
                        style={
                            "backgroundColor": "color-mix(in srgb, var(--mantine-primary-color-filled), var(--mantine-color-body) 90%)",
                        },
                    ),
                    dmc.AppShellNavbar(
                        navbar_content,
                        style={
                            "backgroundColor": "color-mix(in srgb, var(--mantine-primary-color-filled), transparent 95%)",
                        },
                    ),
                    dmc.AppShellMain(children=page_container),
                ],
                navbar={
                    "width": 300,
                    "breakpoint": "sm",
                    "collapsed": {"mobile": True},
                },
                header={"height": 60},
                padding="md",
            ),
            dcc.Store(id="collection-store", storage_type="local", data=[]),
            dcc.Store(
                id="theme-store",
                storage_type="local",
                data=get_setting("theme", "dark"),
            ),
            dcc.Store(
                id="primary-color-store",
                storage_type="local",
                data=get_setting("primary_color", "blue"),
            ),
        ],
    )

    return app


@callback(
    Output("app-shell", "navbar"),
    Input("url", "pathname"),
    State("app-shell", "navbar"),
)
def toggle_navbar(
    pathname: str, current_navbar: dict[str, Any]
) -> dict[str, Any]:
    """Hide the navbar when on the settings page."""
    new_navbar = current_navbar or {}
    is_settings = pathname == "/settings"
    new_navbar["collapsed"] = {"mobile": True, "desktop": is_settings}
    return new_navbar


@callback(
    Output("mantine-provider", "forceColorScheme"),
    Output("mantine-provider", "theme"),
    Input("theme-store", "data"),
    Input("primary-color-store", "data"),
    State("mantine-provider", "theme"),
)
def update_global_theme(
    theme_val: str | None, color: str | None, current_theme: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Update the Mantine theme and primary color globally."""
    new_theme = current_theme or {}
    new_theme["primaryColor"] = color or "blue"
    return theme_val or "dark", new_theme


if __name__ == "__main__":
    dash_app = generate_app()
    dash_app.run(debug=True, use_reloader=False)
