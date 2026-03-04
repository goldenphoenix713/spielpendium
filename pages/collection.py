import base64

import dash
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc, html

from api.bgg_api_interface import get_user_game_collection

dash.register_page(__name__, path="/collection")


def get_b64_image(image_bytes: bytes) -> str:
    """Converts bytes to base64 data URI."""
    if not image_bytes:
        return ""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def create_game_card(game, ownership_status) -> dmc.Card:
    """Creates a card component for a single game."""
    return dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Image(
                    # Use thumbnail for the grid view for better performance
                    src=get_b64_image(game.thumbnail or game.image)
                    if (game.thumbnail or game.image)
                    else "https://placehold.co/200x200?text=No+Image",
                    h=200,
                    fit="contain",
                ),
            ),
            dmc.Group(
                [
                    dmc.Text(game.name, fw=500, lineClamp=1),
                    dmc.Badge(
                        f"{game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
                        color="yellow",
                        variant="light",
                    ),
                ],
                justify="space-between",
                mt="md",
                mb="xs",
            ),
            dmc.Text(
                f"{game.min_players}-{game.max_players} Players • {game.min_play_time}-{game.max_play_time} Min",
                size="sm",
                c="dimmed",
            ),
            dmc.Button(
                "Details",
                variant="light",
                color="blue",
                fullWidth=True,
                mt="md",
                radius="md",
                id={"type": "game-card", "index": game.bgg_id},
            ),
        ],
        withBorder=True,
        shadow="sm",
        radius="md",
        w="100%",
    )


layout = dmc.Container(
    [
        dmc.Title("My Collection", order=2, mb="lg"),
        html.Div(
            style={"position": "relative", "minHeight": "200px"},
            children=[
                dmc.LoadingOverlay(
                    id="loading-collection",
                    overlayProps={"radius": "sm", "blur": 2},
                    visible=True,
                ),
                html.Div(id="collection-grid"),
            ],
        ),
        dmc.Modal(
            title=dmc.Group(
                [
                    dmc.Title(id="modal-game-title", order=2),
                    dmc.Badge(
                        id="modal-game-rating", color="yellow", size="lg"
                    ),
                ],
                justify="space-between",
                w="100%",
            ),
            id="game-detail-modal",
            size="70%",
            zIndex=10000,
            children=[
                dmc.LoadingOverlay(
                    id="loading-modal",
                    visible=False,
                ),
                html.Div(
                    id="modal-game-content", style={"minHeight": "300px"}
                ),
            ],
        ),
        dcc.Store(id="collection-data-store"),
    ],
    fluid=True,
)


@callback(
    Output("game-detail-modal", "opened"),
    Output("modal-game-title", "children"),
    Output("modal-game-rating", "children"),
    Output("modal-game-content", "children"),
    Output("loading-modal", "visible"),
    Input({"type": "game-card", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_modal(n_clicks):
    if not any(n_clicks):
        return False, "", "", "", False

    ctx = dash.callback_context
    triggered_id = ctx.triggered_id["index"]

    # Fetch game details from DB (they should be there since we synced the collection)
    from sqlmodel import Session, select

    from util.database.models import (
        Game,
        engine,
    )

    with Session(engine) as session:
        game = session.exec(
            select(Game).where(Game.bgg_id == triggered_id)
        ).first()
        if not game:
            return (
                True,
                "Error",
                "",
                "Game details not found in database.",
                False,
            )

        # Prepare description (BeautifulSoup text cleaning was done on ingestion)
        description_paragraphs = [
            html.P(p) for p in game.description.split("\n") if p.strip()
        ]

        # Get Authors and Artists
        authors = [p.name for p in game.authors]
        artists = [p.name for p in game.artists]
        publishers = [pub.name for pub in game.publishers]
        categories = [cat.name for cat in game.categories]

        content = dmc.Grid([
            dmc.GridCol(
                dmc.Image(
                    # Use full image for the detail modal
                    src=get_b64_image(game.image or game.thumbnail),
                    radius="md",
                    fit="contain",
                    style={"maxHeight": "400px"},
                ),
                span=4,
            ),
            dmc.GridCol(
                dmc.Stack([
                    dmc.Group(
                        [
                            dmc.Text(f"Year: {game.release_year}", fw=700),
                            dmc.Text(
                                f"Players: {game.min_players}-{game.max_players}",
                                fw=700,
                            ),
                            dmc.Text(
                                f"Weight: {game.complexity:.2f}/5", fw=700
                            ),
                        ],
                        gap="xl",
                    ),
                    dmc.Divider(),
                    dmc.ScrollArea(
                        h=200, children=dmc.Stack(description_paragraphs)
                    ),
                    dmc.Divider(),
                    dmc.Grid([
                        dmc.GridCol(
                            dmc.Stack(
                                [
                                    dmc.Text("Designers", fw=700, size="sm"),
                                    dmc.Text(", ".join(authors), size="sm"),
                                ],
                                gap=5,
                            ),
                            span=6,
                        ),
                        dmc.GridCol(
                            dmc.Stack(
                                [
                                    dmc.Text("Artists", fw=700, size="sm"),
                                    dmc.Text(", ".join(artists), size="sm"),
                                ],
                                gap=5,
                            ),
                            span=6,
                        ),
                    ]),
                    dmc.Stack(
                        [
                            dmc.Text("Publishers", fw=700, size="sm"),
                            dmc.Text(", ".join(publishers), size="sm"),
                        ],
                        gap=5,
                    ),
                    dmc.Group([
                        dmc.Badge(cat, variant="outline") for cat in categories
                    ]),
                ]),
                span=8,
            ),
        ])

        return (
            True,
            game.name,
            f"Rating: {game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
            content,
            False,
        )


@callback(
    Output("collection-grid", "children"),
    Output("loading-collection", "visible"),
    Input(
        "collection-data-store", "data"
    ),  # Dummy input for now, eventually triggers on load
)
def update_grid(_):
    # Hardcoding username for the prototype phase as discussed
    username = "phoenix713"

    # filters={"own": True} ensures we only get owned games
    collection = get_user_game_collection(username, filters={"own": True})

    if not collection or not collection.items:
        return dmc.Alert(
            "No games found in collection or failed to load.",
            title="Error",
            color="red",
        ), False

    cards = []
    # collection.items is a list of CollectionItem, which has .game and .ownership_status
    for item in collection.items:
        if item.game:
            cards.append(create_game_card(item.game, item.ownership_status))

    return dmc.SimpleGrid(
        cols={"base": 1, "sm": 2, "lg": 4, "xl": 5},
        spacing="lg",
        children=cards,
    ), False
