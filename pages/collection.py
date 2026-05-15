from __future__ import annotations

import math
from html import unescape as html_unescape
from typing import TYPE_CHECKING, Any

import dash
import dash_mantine_components as dmc
from dash import (
    ALL,
    Input,
    Output,
    State,
    callback,
    clientside_callback,
    dcc,
    html,
    no_update,
)
from dash_iconify import DashIconify
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from api import get_game_info, get_user_game_collection
from api.bgg_api.game_details import save_game_data_to_db
from config import TEST_USER
from util.filters import apply_filters_and_sort, game_to_dict
from util.models import (
    Collection,
    CollectionItem,
    Game,
    RelatedGame,
    engine,
)

if TYPE_CHECKING:
    from dash import NoUpdate

    from util.models import OwnershipStatus

dash.register_page(__name__, path="/collection")  # type: ignore[no-untyped-call]

PAGE_SIZE = 50


def create_game_card(
    game: Game, ownership_status: OwnershipStatus | None
) -> html.Div:
    """Creates a card component for a single game."""
    return html.Div(
        dmc.Card(
            children=[
                dmc.CardSection(
                    dmc.Image(
                        src=f"/assets/images/{game.image_path}"
                        if game.image_path
                        else "https://placehold.co/200x200?text=No+Image",
                        h=200,
                        fit="contain",
                    ),
                ),
                dmc.Group(
                    [
                        dmc.Text(game.name, fw=500, lineClamp=1),
                        dmc.Badge(
                            f"{game.bgg_rating:.1f}"
                            if game.bgg_rating
                            else "N/A",
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
                        # TODO: Change the number of players to only one value if min and max are the same
                        # Also do the same for the time.
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
                ),
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            w="100%",
        ),
        id={"type": "game-card", "index": game.bgg_id},
        n_clicks=0,
        className="game-card-hover",
    )


layout = dmc.Container(
    [
        dmc.Title("My Collection", order=2, mb="lg"),
        dmc.Group(
            justify="space-between",
            mb="xs",
            children=[
                dmc.Button(
                    "Refresh Database",
                    id="refresh-database-btn",
                    leftSection=DashIconify(icon="tabler:refresh", width=16),
                    variant="light",
                    color="blue",
                    size="xs",
                ),
                dmc.Text("", id="result-count", size="sm", c="dimmed"),
            ],
        ),
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
        dmc.Group(
            dmc.Pagination(
                id="collection-pagination", total=1, value=1, mt="xl", mb="xl"
            ),
            justify="center",
        ),
        dcc.Store(id="filtered-collection-store", data=[]),
        dmc.Modal(
            title=dmc.Group(
                [
                    dmc.Group(
                        [
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="tabler:arrow-left", width=20
                                ),
                                id="modal-back-button",
                                variant="subtle",
                                color="gray",
                                disabled=True,
                            ),
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="tabler:arrow-right", width=20
                                ),
                                id="modal-forward-button",
                                variant="subtle",
                                color="gray",
                                disabled=True,
                            ),
                            dmc.Title(id="modal-game-title", order=2),
                            dmc.Badge(
                                id="modal-game-rating",
                                color="yellow",
                                size="lg",
                            ),
                        ],
                        gap="sm",
                    ),
                    dmc.Anchor(
                        dmc.Button(
                            "View on BGG",
                            variant="outline",
                            size="xs",
                            rightSection=DashIconify(
                                icon="tabler:external-link", width=14
                            ),
                        ),
                        id="modal-bgg-link",
                        href="#",
                        target="_blank",
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
                    overlayProps={"radius": "sm", "blur": 2},
                ),
                html.Div(
                    id="modal-game-content", style={"minHeight": "300px"}
                ),
            ],
        ),
        dcc.Store(id="collection-data-store"),
        dcc.Store(
            id="modal-history-store",
            data={"history": [], "current_index": -1},
        ),
    ],
    fluid=True,
)


clientside_callback(
    """
    function(title) {
        const modalBody = document.querySelector('.mantine-Modal-body');
        if (modalBody) {
            modalBody.scrollTo({top: 0, behavior: 'instant'});
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("modal-game-title", "id"),
    Input("modal-game-title", "children"),
)


@callback(
    Output("game-detail-modal", "opened"),
    Output("modal-game-title", "children"),
    Output("modal-game-rating", "children"),
    Output("modal-game-content", "children"),
    Output("modal-bgg-link", "href"),
    Output("loading-modal", "visible"),
    Output("modal-history-store", "data"),
    Output("modal-back-button", "disabled"),
    Output("modal-forward-button", "disabled"),
    Input({"type": "game-card", "index": ALL}, "n_clicks"),
    Input({"type": "related-game-link", "index": ALL}, "n_clicks"),
    Input("modal-back-button", "n_clicks"),
    Input("modal-forward-button", "n_clicks"),
    Input("game-detail-modal", "opened"),
    State("modal-history-store", "data"),
    prevent_initial_call=True,
)
def open_modal(
    card_clicks: list[int | None] | None,
    link_clicks: list[int | None] | None,
    back_clicks: int | None,
    forward_clicks: int | None,
    modal_opened: bool,
    history_data: dict[str, Any],
) -> (
    tuple[bool, str, str, Any, str, bool, dict[str, Any], bool, bool]
    | NoUpdate
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered_id
    trigger = ctx.triggered[0]

    # Handle Modal Close (Reset History) - This has priority and value can be False
    if triggered_id == "game-detail-modal" and not modal_opened:
        return (
            False,
            "",
            "",
            "",
            "#",
            False,
            {"history": [], "current_index": -1},
            True,
            True,
        )

    # For all other triggers (clicks), ensure it's a real interaction (value > 0)
    if trigger["value"] is None or trigger["value"] == 0:
        return no_update
    history = history_data.get("history", [])
    current_index = history_data.get("current_index", -1)

    bgg_id = None

    if isinstance(triggered_id, dict):
        # Card or Link click
        bgg_id = triggered_id["index"]
        # Add to history if it's new or different from current
        if current_index == -1 or history[current_index] != bgg_id:
            # If we were in the middle of history, truncate the "forward" part
            history = history[: current_index + 1]
            history.append(bgg_id)
            current_index = len(history) - 1
    elif triggered_id == "modal-back-button":
        if current_index > 0:
            current_index -= 1
            bgg_id = history[current_index]
    elif triggered_id == "modal-forward-button":
        if current_index < len(history) - 1:
            current_index += 1
            bgg_id = history[current_index]
    elif triggered_id == "game-detail-modal" and modal_opened:
        # This can happen if the modal opens but nothing triggered it?
        # Should be handled by card_clicks check below.
        pass

    if bgg_id is None:
        return no_update

    # Prepare history data for return
    updated_history_data = {"history": history, "current_index": current_index}
    back_disabled = current_index <= 0
    forward_disabled = current_index >= len(history) - 1

    # Fetch game details from DB

    # We need to distinguish if this was a card click or a link click
    # but the bgg_id is the index in both cases.

    # Fetch game details from DB
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.bgg_id == bgg_id)).first()

        if not game or not game.description:
            game_data = get_game_info(bgg_id)
            save_game_data_to_db(game_data["items"]["item"])
            session.commit()
            test_game = session.exec(
                select(Game).where(Game.bgg_id == bgg_id)
            ).first()
            if test_game is None:
                return (
                    True,
                    "Error",
                    "",
                    "Game was unable to be added to the database.",
                    "#",
                    False,
                    updated_history_data,
                    back_disabled,
                    forward_disabled,
                )
            game = test_game

        # Get User's Collection ID
        user_collection = session.exec(
            select(Collection).where(Collection.username == TEST_USER)
        ).first()
        user_col_id = user_collection.id if user_collection else None

        # Prepare description
        raw_description = game.description or ""
        clean_description = html_unescape(raw_description).replace("\xad", "")
        description_paragraphs = [
            html.P(p) for p in clean_description.split("\n") if p.strip()
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
            .options(selectinload(RelatedGame.relationship_type))  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501
        ).all()
        related_games_accordion = None
        if related_links:
            # Group by relationship type
            by_type: dict[str, list[tuple[Game, str | None]]] = {}
            for link in related_links:
                rel_type = link.relationship_type.type
                if rel_type not in by_type:
                    by_type[rel_type] = []

                target_game = session.get(Game, link.target_game_id)
                if target_game:
                    owned_status: str | None = None
                    if user_col_id:
                        owned_item = session.exec(
                            select(CollectionItem)
                            .where(
                                CollectionItem.collection_id == user_col_id,
                                CollectionItem.game_id == target_game.id,
                            )
                            .options(
                                selectinload(CollectionItem.ownership_status)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
                            )
                        ).first()
                        if owned_item and owned_item.ownership_status:
                            owned_status = owned_item.ownership_status.name

                    by_type[rel_type].append((target_game, owned_status))

            # Map technical BGG types to readable names
            rel_name_map = {
                "boardgameexpansion": "Expansions / Base Game",
                "boardgamereimplementation": "Reimplementations / Editions",
                "boardgameintegration": "Integrations",
                "boardgamecompilation": "Compilations",
                "boardgameaccessory": "Accessories",
            }

            accordion_items = []
            for rel_type, games in sorted(by_type.items()):
                display_name = rel_name_map.get(
                    rel_type,
                    rel_type.replace("boardgame", " ").title().strip(),
                )
                item_content = dmc.Group(
                    [
                        dmc.Group(
                            [
                                html.Span(
                                    g.name,
                                    id={
                                        "type": "related-game-link",
                                        "index": g.bgg_id,
                                    },
                                    n_clicks=0,
                                    style={
                                        "cursor": "pointer",
                                        "textDecoration": "underline",
                                        "color": "var(--mantine-color-blue-filled)",
                                    },
                                ),
                                dmc.Badge(
                                    "Owned",
                                    color="green",
                                    size="xs",
                                    variant="light",
                                )
                                if status == "owned"
                                else (
                                    dmc.Badge(
                                        "Prev. Owned",
                                        color="gray",
                                        size="xs",
                                        variant="light",
                                    )
                                    if status == "prevowned"
                                    else None
                                ),
                            ],
                            gap=5,
                        )
                        for g, status in sorted(games, key=lambda x: x[0].name)
                    ],
                    gap="xs",
                )

                accordion_items.append(
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                f"{display_name} ({len(games)})"
                            ),
                            dmc.AccordionPanel(item_content),
                        ],
                        value=rel_type,
                    )
                )

            related_games_accordion = dmc.Stack(
                [
                    dmc.Divider(label="Related Games", labelPosition="center"),
                    dmc.Accordion(
                        children=accordion_items,
                        variant="separated",
                        radius="md",
                    ),
                ],
                mt="xl",
            )

        content = html.Div([
            dmc.Grid([
                dmc.GridCol(
                    dmc.Image(
                        src=f"/assets/images/{game.image_path}"
                        if game.image_path
                        else "https://placehold.co/400x400?text=No+Image",
                        radius="md",
                        fit="contain",
                        style={"maxHeight": "400px", "width": "100%"},
                    ),
                    span=4,
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Group(
                            [
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="tabler:calendar",
                                            width=18,
                                            color="gray",
                                        ),
                                        dmc.Text(f"{game.release_year}"),
                                    ],
                                    gap=5,
                                ),
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="tabler:users",
                                            width=18,
                                            color="gray",
                                        ),
                                        dmc.Text(
                                            f"{game.min_players}-{game.max_players}"
                                        ),
                                    ],
                                    gap=5,
                                ),
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="tabler:weight",
                                            width=18,
                                            color="gray",
                                        ),
                                        dmc.Text(
                                            f"{game.complexity:.2f}/5"
                                            if game.complexity
                                            else "N/A"
                                        ),
                                    ],
                                    gap=5,
                                ),
                            ],
                            gap="xl",
                        ),
                        dmc.Divider(),
                        dmc.ScrollArea(
                            h=250,
                            children=dmc.Stack(description_paragraphs),
                            type="auto",
                        ),
                        dmc.Divider(),
                        dmc.Grid([
                            dmc.GridCol(
                                dmc.Stack(
                                    [
                                        dmc.Text(
                                            "Designers", fw=700, size="sm"
                                        ),
                                        dmc.Text(
                                            ", ".join(authors), size="sm"
                                        ),
                                    ],
                                    gap=2,
                                ),
                                span=6,
                            ),
                            dmc.GridCol(
                                dmc.Stack(
                                    [
                                        dmc.Text("Artists", fw=700, size="sm"),
                                        dmc.Text(
                                            ", ".join(artists), size="sm"
                                        ),
                                    ],
                                    gap=2,
                                ),
                                span=6,
                            ),
                        ]),
                        dmc.Stack(
                            [
                                dmc.Text("Publishers", fw=700, size="sm"),
                                dmc.Text(", ".join(publishers), size="sm"),
                            ],
                            gap=2,
                        ),
                        dmc.Group(
                            [
                                dmc.Badge(
                                    cat,
                                    variant="outline",
                                    color="gray",
                                    size="sm",
                                )
                                for cat in categories
                            ],
                            gap="xs",
                        ),
                    ]),
                    span=8,
                ),
            ]),
            related_games_accordion,
        ])

        return (
            True,
            game.name,
            f"Rating: {game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
            content,
            f"https://boardgamegeek.com/boardgame/{game.bgg_id}",
            False,
            updated_history_data,
            back_disabled,
            forward_disabled,
        )


@callback(
    Output("collection-store", "data"),
    Input("collection-data-store", "data"),
    Input("refresh-database-btn", "n_clicks"),
    running=[
        (Output("refresh-database-btn", "loading"), True, False),
    ],
)
def load_collection_store(
    _: Any, _n_clicks: int | None
) -> list[dict[str, Any]]:
    """Load the user's collection into the shared dcc.Store."""
    force_update = dash.ctx.triggered_id == "refresh-database-btn" and bool(
        _n_clicks
    )

    collection = get_user_game_collection(
        TEST_USER,
        filters={},  # Pass empty dict to load all ownership statuses (bypasses own=1 default)
        force_update=force_update,
    )
    if not collection or not collection.items:
        return []
    return [
        game_to_dict(item.game, item.ownership_status)
        for item in collection.items
        if item.game
    ]


@callback(
    Output("filtered-collection-store", "data"),
    Output("result-count", "children"),
    Output("collection-pagination", "value"),
    Output("collection-pagination", "total"),
    Input("collection-store", "data"),
    Input("filters-store", "data"),
)
def filter_collection(
    games: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], str, int, int]:
    """Filter and sort the collection, then calculate pagination bounds."""
    if not games:
        return [], "", 1, 1

    filtered = apply_filters_and_sort(games, filters or {})

    total = len(games)
    shown = len(filtered)
    count_text = f"Showing {shown} of {total} games"

    total_pages = max(1, math.ceil(shown / PAGE_SIZE))

    return filtered, count_text, 1, total_pages


@callback(
    Output("collection-grid", "children"),
    Output("loading-collection", "visible"),
    Output("collection-pagination", "style"),
    Input("filtered-collection-store", "data"),
    Input("collection-pagination", "value"),
)
def render_grid(
    filtered: list[dict[str, Any]],
    page: int | None,
) -> tuple[Any, bool, dict[str, str]]:
    """Render the current page of the filtered game grid."""
    if not filtered:
        return (
            dmc.Alert(
                "No games match the current filters or failed to load.",
                title="No Results",
                color="yellow",
            ),
            False,
            {"display": "none"},
        )

    page = page or 1
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_games = filtered[start_idx:end_idx]

    # Build cards from the serialized dicts (no DB access needed)
    cards = [
        html.Div(
            dmc.Card(
                children=[
                    dmc.CardSection(
                        dmc.Image(
                            src=f"/assets/images/{g['image_path']}"
                            if g.get("image_path")
                            else "https://placehold.co/200x200?text=No+Image",
                            h=200,
                            fit="contain",
                        ),
                    ),
                    dmc.Group(
                        [
                            dmc.Text(g["name"], fw=500, lineClamp=1),
                            dmc.Badge(
                                f"{g['bgg_rating']:.1f}"
                                if g.get("bgg_rating")
                                else "N/A",
                                color="yellow",
                                variant="light",
                            ),
                        ],
                        justify="space-between",
                        mt="md",
                        mb="xs",
                    ),
                    dmc.Text(
                        f"{g['min_players']}-{g['max_players']} Players "
                        f"• {g['min_play_time']}-{g['max_play_time']} Min",
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
                    ),
                ],
                withBorder=True,
                shadow="sm",
                radius="md",
                w="100%",
            ),
            id={"type": "game-card", "index": g["bgg_id"]},
            n_clicks=0,
            className="game-card-hover",
        )
        for g in page_games
    ]

    pagination_style = (
        {"display": "none"} if len(filtered) <= PAGE_SIZE else {}
    )

    return (
        dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "lg": 4, "xl": 5},
            spacing="lg",
            children=cards,
        ),
        False,
        pagination_style,
    )
