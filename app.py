import dash_mantine_components as dmc

# noinspection PyProtectedMember
from dash import Dash, _dash_renderer, page_container
from dash_iconify import DashIconify

from util.models import create_db_and_tables

# noinspection PyProtectedMember
_dash_renderer._set_react_version("18.2.0")  # type: ignore[no-untyped-call]


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
                DashIconify(icon="game-icons:meeple", width=30),
                dmc.Title("Spielpendium", order=3),
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

    # Navbar content
    navbar_content = dmc.Stack(
        justify="space-between",
        h="100%",
        children=[
            dmc.Stack(
                gap="xs",
                p="md",
                children=[
                    dmc.NavLink(
                        label="Collection",
                        leftSection=DashIconify(icon="game-icons:card-draw"),
                        href="/collection",
                        active=True,  # Logic to handle active state needed
                    ),
                    dmc.NavLink(
                        label="Statistics",
                        leftSection=DashIconify(icon="game-icons:histogram"),
                        href="/stats",
                        disabled=True,
                    ),
                    dmc.NavLink(
                        label="Settings",
                        leftSection=DashIconify(icon="game-icons:gears"),
                        href="/settings",
                        disabled=True,
                    ),
                ],
            ),
            dmc.Stack(
                align="center",
                mb="md",
                children=[
                    dmc.Anchor(
                        dmc.Image(
                            src="assets/powered-by-bgg-reversed-rgb.svg",
                            w=150,
                            fit="contain",
                        ),
                        href="https://boardgamegeek.com/",
                        target="_blank",
                    )
                ],
            ),
        ],
    )

    app.layout = dmc.MantineProvider(
        forceColorScheme="dark",
        children=dmc.AppShell(
            [
                dmc.AppShellHeader(header_content, px="md"),
                dmc.AppShellNavbar(navbar_content),
                dmc.AppShellMain(children=page_container),
            ],
            header={"height": 60},
            navbar={
                "width": 300,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
            padding="md",
        ),
    )

    return app


if __name__ == "__main__":
    dash_app = generate_app()
    dash_app.run(debug=True)
