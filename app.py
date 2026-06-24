from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

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
    no_update,
    page_container,
)
from dash_iconify import DashIconify
from loguru import logger as log

import util.filters  # noqa: F401 — registers filter callbacks
from util.filters import generate_drawer_content, generate_sidebar
from util.models import create_db_and_tables

if TYPE_CHECKING:
    from dash import (
        NoUpdate,
    )

# noinspection PyProtectedMember
_dash_renderer._set_react_version("18.2.0")  # type: ignore  # ty: ignore[unused-type-ignore-comment, unused-ignore-comment]


def generate_app() -> Dash:
    log.info("generate_app: Starting Spielpendium application...")
    # Ensure database and tables exist on startup (skip during testing to avoid xdist race conditions)
    if "pytest" not in sys.modules:
        create_db_and_tables()

    log.info("generate_app: Initializing Dash application...")
    app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

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
                    hiddenFrom="md",
                ),
                DashIconify(icon="game-icons:meeple", width=30),
                dmc.Title("Spielpendium", order=3, mr="xl"),
                dmc.Divider(orientation="vertical", h=25, visibleFrom="md"),
                dmc.Group(
                    gap="xs",
                    p="md",
                    visibleFrom="md",
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
                        dmc.Anchor(
                            dmc.Button(
                                "Statistics",
                                leftSection=DashIconify(
                                    icon="game-icons:histogram", width=16
                                ),
                                variant="subtle",
                            ),
                            href="/statistics",
                            underline="never",
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
                        dmc.Anchor(
                            dmc.Button(
                                "BGG Profile",
                                leftSection=DashIconify(
                                    icon="simple-icons:boardgamegeek", width=16
                                ),
                                variant="subtle",
                                color="orange",
                            ),
                            id="header-bgg-profile-link",
                            href="https://boardgamegeek.com/collection/user/",
                            target="_blank",
                            underline="never",
                        ),
                    ],
                ),
            ]),
            # Desktop GitHub link
            dmc.Anchor(
                dmc.ActionIcon(
                    DashIconify(icon="radix-icons:github-logo", width=20),
                    variant="subtle",
                    color="gray",
                    size="lg",
                ),
                href="https://github.com/goldenphoenix713/spielpendium",
                target="_blank",
                visibleFrom="md",
            ),
            # Mobile Navigation & GitHub dropdown Menu
            dmc.Box(
                dmc.Menu(
                    [
                        dmc.MenuTarget(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="tabler:dots-vertical", width=20
                                ),
                                variant="subtle",
                                color="gray",
                                size="lg",
                            )
                        ),
                        dmc.MenuDropdown([
                            dmc.MenuItem(
                                "Collection",
                                leftSection=DashIconify(
                                    icon="game-icons:card-draw", width=16
                                ),
                                href="/collection",
                            ),
                            dmc.MenuItem(
                                "Statistics",
                                leftSection=DashIconify(
                                    icon="game-icons:histogram", width=16
                                ),
                                href="/statistics",
                            ),
                            dmc.MenuItem(
                                "Settings",
                                leftSection=DashIconify(
                                    icon="game-icons:gears", width=16
                                ),
                                href="/settings",
                            ),
                            dmc.MenuItem(
                                "BGG Profile",
                                leftSection=DashIconify(
                                    icon="simple-icons:boardgamegeek", width=16
                                ),
                                id="mobile-bgg-profile-link",
                                href="https://boardgamegeek.com/collection/user/",
                                target="_blank",
                            ),
                            dmc.MenuDivider(),
                            dmc.MenuItem(
                                "GitHub Repository",
                                leftSection=DashIconify(
                                    icon="radix-icons:github-logo", width=16
                                ),
                                href="https://github.com/goldenphoenix713/spielpendium",
                                target="_blank",
                            ),
                        ]),
                    ],
                    position="bottom-end",
                    shadow="md",
                ),
                hiddenFrom="md",
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
        forceColorScheme="dark",
        theme={"primaryColor": "blue"},
        children=[
            dmc.NotificationProvider(position="top-right"),
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
                    "breakpoint": "md",
                    "collapsed": {"mobile": True, "desktop": True},
                },
                header={"height": 60, "collapsed": True},
                padding="md",
            ),
            dcc.Store(id="collection-store", storage_type="local", data=[]),
            dcc.Store(
                id="active-user-store",
                storage_type="local",
                data="",
            ),
            dcc.Store(
                id="theme-store",
                storage_type="local",
                data="dark",
            ),
            dcc.Store(
                id="primary-color-store",
                storage_type="local",
                data="blue",
            ),
            dcc.Store(
                id="managed-users-store",
                storage_type="local",
                data=[],
            ),
            dcc.Store(
                id="layout-view-store",
                storage_type="local",
                data="grid",
            ),
            dcc.Store(
                id="auto-refresh-store",
                storage_type="local",
                data=False,
            ),
            dcc.Store(
                id="page-size-store",
                storage_type="local",
                data=50,
            ),
            dcc.Store(id="sync-trigger-store", data=0),
        ],
    )

    log.info(
        "generate_app: Application layout and stores successfully initialized."
    )
    return app


@callback(
    Output("app-shell", "navbar"),
    Output("app-shell", "header"),
    Output("burger-button", "style"),
    Input("url", "pathname"),
    Input("active-user-store", "data"),
    State("app-shell", "navbar"),
    State("app-shell", "header"),
)
def toggle_ui_elements(
    pathname: str,
    active_user: str | None,
    current_navbar: dict[str, Any],
    current_header: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Hide UI elements during onboarding or on the settings page."""
    log.debug(
        f"toggle_ui_elements: Route changed to '{pathname}' (active_user: '{active_user}')"
    )
    new_navbar = current_navbar or {}
    new_header = current_header or {}

    # If no user, hide everything except main content
    if not active_user:
        new_navbar["collapsed"] = {"mobile": True, "desktop": True}
        new_header["collapsed"] = True
        return new_navbar, new_header, {"display": "none"}

    # Otherwise, show header and handle navbar based on page
    new_header["collapsed"] = False
    is_collection = pathname == "/collection"

    # Hide the sidebar filters on all pages except /collection
    new_navbar["collapsed"] = {"mobile": True, "desktop": not is_collection}

    # Also hide the burger menu toggler icon on non-collection pages
    burger_style = {} if is_collection else {"display": "none"}

    return new_navbar, new_header, burger_style


@callback(
    Output("url", "pathname"),
    Input("active-user-store", "data"),
    State("url", "pathname"),
)
def onboarding_redirect(
    active_user: str | None, pathname: str
) -> str | NoUpdate:
    """Redirect to landing page if no user is connected."""
    if not active_user and pathname != "/":
        log.warning(
            f"onboarding_redirect: No active user. Redirecting from '{pathname}' to onboarding page '/'"
        )
        return "/"
    return no_update


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
    log.info(
        f"update_global_theme: Applying theme '{theme_val}' and primary color '{color}'"
    )
    new_theme = current_theme or {}
    new_theme["primaryColor"] = color or "blue"
    return theme_val or "dark", new_theme


@callback(
    Output("header-bgg-profile-link", "href"),
    Output("mobile-bgg-profile-link", "href"),
    Input("active-user-store", "data"),
)
def update_header_bgg_link(username: str | None) -> tuple[str, str]:
    """Update the BGG profile link in the header when the active user changes."""
    log.info(
        f"update_header_bgg_link: Updating BGG profile links for user '{username}'"
    )
    url = f"https://boardgamegeek.com/collection/user/{username or ''}"
    return url, url


dash_app = generate_app()
server = dash_app.server


@server.route("/healthz")  # type: ignore[untyped-decorator]
def healthz() -> tuple[str, int]:
    """Lightweight health check endpoint for Render."""
    return "OK", 200


@server.route("/download/pdf/<filename>")  # type: ignore[untyped-decorator]
def download_pdf(filename: str) -> Any:
    """Serve the generated PDF catalog from a non-watched temp directory as a download attachment."""
    import os
    import tempfile

    from flask import send_from_directory

    directory = os.path.join(tempfile.gettempdir(), "spielpendium_exports")
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    dash_app.run(debug=True, use_reloader=False)
