import dash_mantine_components as dmc

# noinspection PyProtectedMember
from dash import Dash, _dash_renderer, dcc, page_container
from dash_iconify import DashIconify

import util.filters  # noqa: F401 — registers filter callbacks
from util.filters import generate_sidebar
from util.models import create_db_and_tables

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
                DashIconify(icon="game-icons:meeple", width=30),
                dmc.Title("Spielpendium", order=3),
                dmc.Group(
                    gap="xs",
                    p="md",
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
                        dmc.Button(
                            "Settings",
                            leftSection=DashIconify(
                                icon="game-icons:gears", width=16
                            ),
                            variant="subtle",
                            disabled=True,
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

    app.layout = dmc.MantineProvider(
        forceColorScheme="dark",
        children=dmc.AppShell(
            [
                dmc.AppShellHeader(header_content, px="md"),
                dmc.AppShellNavbar(navbar_content),
                dmc.AppShellMain(children=page_container),
                dcc.Store(
                    id="collection-store", storage_type="local", data=[]
                ),
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
    dash_app.run(debug=True, use_reloader=False)
