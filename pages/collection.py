from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dash
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc, html
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from api.bgg_api_interface import get_user_game_collection
from config import TEST_USER
from util.images import get_b64_image
from util.models import (
    Collection,
    CollectionItem,
    Game,
    RelatedGame,
    engine,
)

if TYPE_CHECKING:
    from util.models import OwnershipStatus

dash.register_page(__name__, path="/collection")  # type: ignore[no-untyped-call]


def create_game_card(
    game: Game, ownership_status: OwnershipStatus | None
) -> dmc.Card:
    """Creates a card component for a single game."""
    return dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Image(
                    src=get_b64_image(game.image)
                    if game.image
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
                (
                    f"{game.min_players}-{game.max_players} Players •"
                    f" {game.min_play_time}-{game.max_play_time} Min"
                ),
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
    Input({"type": "related-game-link", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_modal(
    card_clicks: list[int | None] | None, link_clicks: list[int | None] | None
) -> tuple[bool, str, str, Any, bool]:
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", "", "", False

    # Make sure we have an actual trigger and not a creation
    card_missing = card_clicks is None or all(x is None for x in card_clicks)
    link_missing = link_clicks is None or all(x is None for x in link_clicks)

    if card_missing and link_missing:
        return False, "", "", "", False

    triggered_id = ctx.triggered_id["index"]

    # We need to distinguish if this was a card click or a link click
    # but the bgg_id is the index in both cases.

    # Fetch game details from DB
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

        # Get User's Collection ID
        user_collection = session.exec(
            select(Collection).where(Collection.username == TEST_USER)
        ).first()
        user_col_id = user_collection.id if user_collection else None

        # Prepare description
        description_paragraphs = [
            html.P(p) for p in game.description.split("\n") if p.strip()
        ]

        # Get Authors and Artists
        authors = [p.name for p in game.authors]
        artists = [p.name for p in game.artists]
        publishers = [pub.name for pub in game.publishers]
        categories = [cat.name for cat in game.categories]

        # Get Related Games
        related_links = session.exec(
            select(RelatedGame)
            .where(RelatedGame.source_game_id == game.id)
            .options(selectinload(RelatedGame.relationship_type))  # type: ignore[arg-type]
        ).all()

        related_games_sections = []
        if related_links:
            # Group by relationship type
            by_type: dict[str, list[tuple[Game, bool]]] = {}
            for link in related_links:
                rel_type = link.relationship_type.type
                if rel_type not in by_type:
                    by_type[rel_type] = []

                # Fetch target game
                target_game = session.get(Game, link.target_game_id)
                if target_game:
                    # Check if owned
                    owned = False
                    if user_col_id:
                        owned_item = session.exec(
                            select(CollectionItem).where(
                                CollectionItem.collection_id == user_col_id,
                                CollectionItem.game_id == target_game.id,
                            )
                        ).first()
                        owned = owned_item is not None

                    by_type[rel_type].append((target_game, owned))

            for rel_type, games in by_type.items():
                related_games_sections.append(
                    dmc.Stack(
                        [
                            dmc.Text(
                                rel_type.capitalize(),
                                fw=700,
                                size="sm",
                                mt="md",
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        [
                                            g.name,
                                            dmc.Badge(
                                                "Owned",
                                                color="green",
                                                size="xs",
                                                ml=5,
                                            )
                                            if is_owned
                                            else None,
                                        ],
                                        variant="subtle",
                                        color="gray",
                                        size="compact-xs",
                                        id={
                                            "type": "related-game-link",
                                            "index": g.bgg_id,
                                        },
                                    )
                                    for g, is_owned in games
                                ],
                                gap="xs",
                            ),
                        ],
                        gap=2,
                    )
                )

        content = dmc.Grid([
            dmc.GridCol(
                dmc.Stack([
                    dmc.Image(
                        # Use full image for the detail modal
                        src=get_b64_image(game.image)
                        if game.image
                        else "https://placehold.co/200x200?text=No+Image",
                        radius="md",
                        fit="contain",
                        style={"maxHeight": "400px"},
                    ),
                    *related_games_sections,
                ]),
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
def update_grid(_: Any) -> tuple[Any, bool]:
    # filters={"own": True} ensures we only get owned games
    collection = get_user_game_collection(TEST_USER, filters={"own": True})

    if not collection or not collection.items:
        return dmc.Alert(
            "No games found in collection or failed to load.",
            title="Error",
            color="red",
        ), False

    # collection.items is a list of CollectionItem, which has .game and
    # .ownership_status
    # TODO: Add a sorting field and have that field be the key in sorted
    cards = [
        create_game_card(item.game, item.ownership_status)
        for item in sorted(collection.items, key=lambda x: x.game.name)
        if item.game
    ]

    return dmc.SimpleGrid(
        cols={"base": 1, "sm": 2, "lg": 4, "xl": 5},
        spacing="lg",
        children=cards,
    ), False
