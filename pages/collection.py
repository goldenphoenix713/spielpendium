from __future__ import annotations

import io
import math
import tempfile
import threading
from html import unescape as html_unescape
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import dash
import dash_mantine_components as dmc
from dash import (
    ALL,
    Input,
    NoUpdate,
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
from util.filters import apply_filters_and_sort, game_to_dict
from util.models import (
    Collection,
    CollectionItem,
    Game,
    GameFamilyLink,
    RelatedGame,
    engine,
)
from util.settings import get_active_username
from util.status import get_sync_status, set_sync_status

if TYPE_CHECKING:
    from dash import NoUpdate

    from util.models import OwnershipStatus

dash.register_page(__name__, path="/collection")  # type: ignore[no-untyped-call]

STATUS_BADGE_CONFIG = {
    "own": {"label": "Own", "color": "hsl(142, 70%, 45%)"},
    "prevowned": {"label": "Previously Owned", "color": "hsl(210, 10%, 60%)"},
    "fortrade": {"label": "For Trade", "color": "hsl(38, 92%, 50%)"},
    "want": {"label": "Want in Trade", "color": "hsl(173, 80%, 40%)"},
    "wanttobuy": {"label": "Want To Buy", "color": "hsl(14, 90%, 55%)"},
    "wanttoplay": {"label": "Want To Play", "color": "hsl(271, 76%, 53%)"},
    "preordered": {"label": "Preordered", "color": "hsl(217, 91%, 60%)"},
    "wishlist": {"label": "Wishlist", "color": "hsl(330, 85%, 60%)"},
}


def create_status_badges(statuses: list[str]) -> list[dmc.Badge]:
    """Create a list of dmc.Badge components for the given statuses."""
    badges = []
    for s in statuses:
        config = STATUS_BADGE_CONFIG.get(s)
        if config:
            badges.append(
                dmc.Badge(
                    config["label"],
                    color=config["color"],
                    variant="light",
                    size="sm",
                )
            )
    return badges


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
                dmc.Box(
                    dmc.Text(
                        game.name,
                        fw=700,
                        size="lg",
                        className="marquee-title",
                    ),
                    className="marquee-container",
                    mt="md",
                ),
                dmc.Group(
                    [
                        dmc.Group(
                            create_status_badges(
                                getattr(game, "temp_statuses", [])
                            ),
                            gap=5,
                        ),
                        dmc.Badge(
                            f"{game.bgg_rating:.1f}"
                            if game.bgg_rating
                            else "N/A",
                            color="yellow",
                            variant="light",
                        ),
                    ],
                    justify="space-between",
                    mt="xs",
                    mb="xs",
                    wrap="nowrap",
                ),
                dmc.Text(
                    (
                        f"{game.min_players}{f'-{game.max_players}' if game.min_players != game.max_players else ''} Players • "
                        f"{game.min_play_time}{f'-{game.max_play_time}' if game.min_play_time != game.max_play_time else ''} Min"
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


def layout() -> dmc.Container:
    return dmc.Container(
        [
            dmc.Title("My Collection", order=2, mb="lg"),
            dmc.Group(
                justify="space-between",
                mb="xs",
                children=[
                    dmc.Group(
                        [
                            dmc.Button(
                                "Refresh Database",
                                id="refresh-database-btn",
                                leftSection=DashIconify(
                                    icon="tabler:refresh", width=16
                                ),
                                variant="light",
                                color="blue",
                                size="xs",
                            ),
                            dmc.Button(
                                "Export PDF",
                                id="export-pdf-btn",
                                leftSection=DashIconify(
                                    icon="tabler:download", width=16
                                ),
                                variant="light",
                                color="green",
                                size="xs",
                            ),
                            dmc.SegmentedControl(
                                id="collection-view-toggle",
                                data=[
                                    {
                                        "value": "grid",
                                        "label": dmc.Center([
                                            DashIconify(
                                                icon="tabler:layout-grid",
                                                width=16,
                                                style={"marginRight": 4},
                                            ),
                                            html.Span("Grid"),
                                        ]),
                                    },
                                    {
                                        "value": "list",
                                        "label": dmc.Center([
                                            DashIconify(
                                                icon="tabler:list-details",
                                                width=16,
                                                style={"marginRight": 4},
                                            ),
                                            html.Span("List"),
                                        ]),
                                    },
                                ],
                                size="xs",
                                value="grid",
                            ),
                        ],
                        gap="sm",
                    ),
                    dmc.Text("", id="result-count", size="sm", c="dimmed"),
                ],
            ),
            dmc.Stack(
                id="sync-progress-container",
                children=[
                    dmc.Progress(
                        id="sync-progress-bar",
                        value=0,
                        striped=True,
                        animated=True,
                        mb="xs",
                    ),
                    dmc.Text(
                        "",
                        id="sync-progress-text",
                        size="xs",
                        c="dimmed",
                        ta="center",
                    ),
                ],
                style={"display": "none"},
                mb="lg",
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
                    id="collection-pagination",
                    total=1,
                    value=1,
                    mt="xl",
                    mb="xl",
                ),
                justify="center",
            ),
            dcc.Store(id="filtered-collection-store", data=[]),
            dcc.Store(id="pdf-generation-trigger-store"),
            html.Div(id="collection-notification-container"),
            dcc.Interval(id="sync-interval", interval=1000, disabled=True),
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
                        dmc.Group(
                            [
                                dmc.Button(
                                    "Sync Game",
                                    id="sync-game-btn",
                                    variant="subtle",
                                    color="blue",
                                    size="xs",
                                    leftSection=DashIconify(
                                        icon="tabler:refresh", width=14
                                    ),
                                ),
                                dmc.Anchor(
                                    dmc.Button(
                                        "View on BGG",
                                        variant="outline",
                                        size="xs",
                                        rightSection=DashIconify(
                                            icon="tabler:external-link",
                                            width=14,
                                        ),
                                    ),
                                    id="modal-bgg-link",
                                    href="#",
                                    target="_blank",
                                ),
                            ],
                            gap="xs",
                        ),
                    ],
                    justify="space-between",
                    w="100%",
                ),
                id="game-detail-modal",
                size="70%",
                zIndex=10000,
                className="responsive-detail-modal",
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
    Output("sync-game-btn", "disabled"),
    Input("active-user-store", "data"),
)
def disable_sync_game_btn_if_no_user(active_user: str | None) -> bool:
    """Disable the sync game button in the modal if no user is connected."""
    return not active_user


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
    Input("sync-game-btn", "n_clicks"),
    State("modal-history-store", "data"),
    State("active-user-store", "data"),
    running=[
        (Output("loading-modal", "visible"), True, False),
        (Output("sync-game-btn", "loading"), True, False),
    ],
    prevent_initial_call=True,
)
def open_modal(
    card_clicks: list[int | None] | None,
    link_clicks: list[int | None] | None,
    back_clicks: int | None,
    forward_clicks: int | None,
    modal_opened: bool,
    sync_clicks: int | None,
    history_data: dict[str, Any],
    active_user: str | None = None,
) -> (
    tuple[
        bool, str, str, Any, str, bool | NoUpdate, dict[str, Any], bool, bool
    ]
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
    elif triggered_id == "sync-game-btn":
        if current_index >= 0:
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
    force_sync = triggered_id == "sync-game-btn"
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.bgg_id == bgg_id)).first()

        if not game or not game.description or force_sync:
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
                    no_update,
                    updated_history_data,
                    back_disabled,
                    forward_disabled,
                )
            game = test_game

        # Get User's Collection ID
        username = active_user or get_active_username()
        user_collection = session.exec(
            select(Collection).where(Collection.username == username)
        ).first()
        user_col_id = user_collection.id if user_collection else None
        # Get statuses for the main game
        main_item = None
        if user_col_id:
            main_item = session.exec(
                select(CollectionItem).where(
                    CollectionItem.collection_id == user_col_id,
                    CollectionItem.game_id == game.id,
                )
            ).first()
        main_statuses = main_item.statuses if main_item else []

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
            .options(selectinload(cast("Any", RelatedGame.relationship_type)))
        ).all()

        # Get Series / Franchise Games
        series_families = [
            f
            for f in game.families
            if f.name.startswith("Game:") or f.name.startswith("Series:")
        ]
        family_games: list[tuple[Game, list[str]]] = []
        if series_families:
            family_ids = [f.id for f in series_families]
            stmt = (
                select(Game)
                .join(GameFamilyLink)
                .where(GameFamilyLink.family_id.in_(family_ids))  # type: ignore[attr-defined] # ty:ignore[unresolved-attribute]
                .where(Game.id != game.id)
            )
            other_games = session.exec(stmt).all()
            seen_ids = set()
            unique_other_games = []
            for og in other_games:
                if og.id not in seen_ids:
                    seen_ids.add(og.id)
                    unique_other_games.append(og)

            for og in unique_other_games:
                og_statuses = []
                if user_col_id:
                    owned_item = session.exec(
                        select(CollectionItem).where(
                            CollectionItem.collection_id == user_col_id,
                            CollectionItem.game_id == og.id,
                        )
                    ).first()
                    if owned_item:
                        og_statuses = owned_item.statuses
                family_games.append((og, og_statuses))

        related_games_accordion = None
        if related_links or family_games:
            by_type: dict[str, list[tuple[Game, list[str]]]] = {}
            if related_links:
                for link in related_links:
                    rel_type = link.relationship_type.type
                    if rel_type not in by_type:
                        by_type[rel_type] = []

                    target_game = session.get(Game, link.target_game_id)
                    if target_game:
                        owned_statuses: list[str] = []
                        if user_col_id:
                            owned_item = session.exec(
                                select(CollectionItem).where(
                                    CollectionItem.collection_id
                                    == user_col_id,
                                    CollectionItem.game_id == target_game.id,
                                )
                            ).first()
                            if owned_item:
                                owned_statuses = owned_item.statuses

                        by_type[rel_type].append((target_game, owned_statuses))

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
                                *create_status_badges(statuses),
                            ],
                            gap=5,
                        )
                        for g, statuses in sorted(
                            games, key=lambda x: x[0].name
                        )
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

            if family_games:
                family_content = dmc.Group(
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
                                *create_status_badges(statuses),
                            ],
                            gap=5,
                        )
                        for g, statuses in sorted(
                            family_games, key=lambda x: x[0].name
                        )
                    ],
                    gap="xs",
                )
                accordion_items.append(
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                f"Series / Franchise ({len(family_games)})"
                            ),
                            dmc.AccordionPanel(family_content),
                        ],
                        value="series_franchise",
                    )
                )

            related_games_accordion = dmc.Stack([
                dmc.Divider(label="Related Games", labelPosition="center"),
                dmc.Accordion(children=accordion_items, variant="separated"),
            ])

        # Re-fetch for modal rendering
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
                    span={"base": 12, "md": 4},
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Title(game.name, order=2),
                        dmc.Group(create_status_badges(main_statuses)),
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
                                            f"{game.min_players}{f'-{game.max_players}' if game.min_players != game.max_players else ''}"
                                        ),
                                    ],
                                    gap=5,
                                ),
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="tabler:clock",
                                            width=18,
                                            color="gray",
                                        ),
                                        dmc.Text(
                                            f"{game.min_play_time}{f'-{game.max_play_time}' if game.min_play_time != game.max_play_time else ''} min"
                                        ),
                                    ],
                                    gap=5,
                                ),
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="tabler:cake",
                                            width=18,
                                            color="gray",
                                        ),
                                        dmc.Text(
                                            f"{game.min_age}+"
                                            if game.min_age
                                            else "Any age"
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
                                span={"base": 12, "xs": 6},
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
                                span={"base": 12, "xs": 6},
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
                    span={"base": 12, "md": 8},
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
            no_update,  # loading-modal visibility handled by 'running'
            updated_history_data,
            back_disabled,
            forward_disabled,
        )


@callback(
    Output("refresh-database-btn", "disabled"),
    Input("active-user-store", "data"),
)
def disable_refresh_btn_if_no_user(active_user: str | None) -> bool:
    """Disable the refresh button if no user is connected."""
    return not active_user


@callback(
    Output("sync-interval", "disabled"),
    Output("sync-progress-container", "style"),
    Output("refresh-database-btn", "loading"),
    Input("refresh-database-btn", "n_clicks"),
    State("active-user-store", "data"),
    State("auto-refresh-store", "data"),
    prevent_initial_call=False,
)
def start_sync(
    n_clicks: int | None,
    active_user: str | None,
    auto_refresh: bool | None = None,
) -> tuple[bool, dict[str, str], bool] | NoUpdate:
    """Starts the collection sync in a background thread."""
    if not active_user:
        return no_update

    should_sync = False
    if n_clicks:  # User clicked the refresh button
        should_sync = True
    else:  # Initial load or active user loaded
        if auto_refresh:
            should_sync = True

    if not should_sync:
        status = get_sync_status(active_user)
        if status.active:
            # Sync is already active in database! Restore UI progress bar and polling interval.
            return False, {"display": "block"}, True
        return no_update

    username = active_user

    def run_sync() -> None:
        try:
            get_user_game_collection(username, filters={}, force_update=True)
        except Exception as e:
            from loguru import logger

            logger.error(f"Sync failed: {e}")
            set_sync_status(username, False, message=f"Error: {e}")

    thread = threading.Thread(target=run_sync)
    thread.daemon = True
    thread.start()

    return False, {"display": "block"}, True


@callback(
    Output("sync-progress-bar", "value"),
    Output("sync-progress-bar", "label"),
    Output("sync-progress-text", "children"),
    Output("sync-interval", "disabled", allow_duplicate=True),
    Output("sync-progress-container", "style", allow_duplicate=True),
    Output("sync-trigger-store", "data"),
    Output("refresh-database-btn", "loading", allow_duplicate=True),
    Output(
        "collection-notification-container", "children", allow_duplicate=True
    ),
    Input("sync-interval", "n_intervals"),
    State("active-user-store", "data"),
    State("sync-trigger-store", "data"),
    prevent_initial_call=True,
)
def update_progress(
    _: int, active_user: str | None, trigger_count: int
) -> tuple[
    int,
    str,
    str,
    bool,
    dict[str, str],
    int,
    bool,
    dmc.Notification | NoUpdate,
]:
    """Polls the sync status and updates the progress bar."""
    status = get_sync_status(active_user or "")

    if not status.active:
        notification_id = f"sync-complete-notification-{trigger_count}"
        is_error = (
            "error" in (status.message or "").lower()
            or "fail" in (status.message or "").lower()
        )

        if is_error:
            notification = dmc.Notification(
                id=notification_id,
                title="Sync Failed",
                message=status.message
                or "An error occurred during synchronization.",
                color="red",
                icon=DashIconify(icon="tabler:x", width=16),
                action="show",
                autoClose=5000,
            )
        else:
            notification = dmc.Notification(
                id=notification_id,
                title="Sync Complete",
                message="Your collection has been synchronized successfully.",
                color="green",
                icon=DashIconify(icon="tabler:check", width=16),
                action="show",
                autoClose=3000,
            )

        return (
            100,
            "100%",
            status.message or "Sync complete!",
            True,
            {"display": "none"},
            trigger_count + 1,
            False,
            notification,
        )

    progress = (status.current / status.total * 100) if status.total > 0 else 0
    return (
        int(progress),
        f"{int(progress)}%",
        status.message,
        False,
        {"display": "block"},
        trigger_count,
        True,
        no_update,
    )


@callback(
    Output("collection-store", "data"),
    Input("sync-trigger-store", "data"),
    Input("active-user-store", "data"),
)
def load_collection_store(
    sync_trigger: int, active_user: str | None
) -> list[dict[str, Any]]:
    """Load the user's collection into the shared dcc.Store."""
    if not active_user:
        return []

    collection = get_user_game_collection(
        active_user,
        filters={},
        force_update=False,  # Already updated by the background thread
    )
    if not collection or not collection.items:
        return []
    return [
        game_to_dict(item.game, item) for item in collection.items if item.game
    ]


@callback(
    Output("filtered-collection-store", "data"),
    Output("result-count", "children"),
    Output("collection-pagination", "value"),
    Output("collection-pagination", "total"),
    Input("collection-store", "data"),
    Input("filters-store", "data"),
    State("page-size-store", "data"),
)
def filter_collection(
    games: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None,
    page_size: int | None = None,
) -> tuple[list[dict[str, Any]], str, int, int]:
    """Filter and sort the collection, then calculate pagination bounds."""
    if not games:
        return [], "", 1, 1

    filtered = apply_filters_and_sort(games, filters or {})

    total = len(games)
    shown = len(filtered)
    count_text = f"Showing {shown} of {total} games"

    p_size = page_size if page_size is not None else 50
    total_pages = max(1, math.ceil(shown / p_size))

    return filtered, count_text, 1, total_pages


@callback(
    Output("collection-grid", "children"),
    Output("loading-collection", "visible"),
    Output("collection-pagination", "style"),
    Input("filtered-collection-store", "data"),
    Input("collection-pagination", "value"),
    Input("active-user-store", "data"),
    Input("collection-view-toggle", "value"),
    State("page-size-store", "data"),
    State("layout-view-store", "data"),
)
def render_grid(
    filtered: list[dict[str, Any]],
    page: int | None,
    active_user: str | None,
    view_mode: str | None = None,
    page_size: int | None = None,
    layout_view: str | None = None,
) -> tuple[Any, bool, dict[str, str]]:
    """Render the current page of the filtered game grid or list."""
    if not active_user:
        return (
            dmc.Alert(
                "Please set a BoardGameGeek username on the Home page to view your collection.",
                title="No User Connected",
                color="blue",
                variant="light",
                icon=DashIconify(icon="tabler:user-plus"),
            ),
            False,
            {"display": "none"},
        )

    if not filtered:
        return (
            dmc.Alert(
                "No games match the current filters or failed to load.",
                title="No Results",
                color="yellow",
                variant="light",
                icon=DashIconify(icon="tabler:search-off"),
            ),
            False,
            {"display": "none"},
        )

    p_size = page_size if page_size is not None else 50

    page = page or 1
    start_idx = (page - 1) * p_size
    end_idx = start_idx + p_size
    page_games = filtered[start_idx:end_idx]

    view_mode = view_mode or layout_view or "grid"

    if view_mode == "list":
        rows = []
        for g in page_games:
            # Thumbnail Image
            img_src = (
                f"/assets/images/{g['image_path']}"
                if g.get("image_path")
                else "https://placehold.co/200x200?text=No+Image"
            )
            thumbnail = dmc.Image(
                src=img_src,
                h=40,
                w=40,
                fit="contain",
                radius="sm",
            )

            # Rating
            rating_text = (
                f"{g['bgg_rating']:.1f}" if g.get("bgg_rating") else "N/A"
            )
            rating_badge = dmc.Badge(
                rating_text,
                color="yellow",
                variant="light",
            )

            # Players text
            players = f"{g['min_players']}" + (
                f"-{g['max_players']}"
                if g["min_players"] != g["max_players"]
                else ""
            )

            # Time text
            play_time = f"{g['min_play_time']}" + (
                f"-{g['max_play_time']}"
                if g["min_play_time"] != g["max_play_time"]
                else ""
            )

            row = html.Tr(
                id={"type": "game-card", "index": g["bgg_id"]},
                n_clicks=0,
                style={"cursor": "pointer"},
                className="game-row-hover",
                children=[
                    dmc.TableTd(thumbnail, style={"width": 60}),
                    dmc.TableTd(
                        dmc.Text(
                            g["name"],
                            fw=700,
                            size="sm",
                            className="list-title-text",
                        ),
                    ),
                    dmc.TableTd(
                        dmc.Badge(
                            f"{players} Players",
                            color="indigo",
                            variant="light",
                            size="sm",
                        )
                    ),
                    dmc.TableTd(
                        dmc.Badge(
                            f"{play_time} Min",
                            color="cyan",
                            variant="light",
                            size="sm",
                        )
                    ),
                    dmc.TableTd(rating_badge),
                    dmc.TableTd(
                        dmc.Group(
                            create_status_badges(g.get("statuses", [])),
                            gap=5,
                        )
                    ),
                    dmc.TableTd(
                        dmc.Button(
                            "Details",
                            size="xs",
                            variant="light",
                            color="blue",
                            radius="sm",
                        ),
                        style={"textAlign": "right", "width": 100},
                    ),
                ],
            )
            rows.append(row)

        content = dmc.Card(
            withBorder=True,
            shadow="sm",
            radius="md",
            p=0,
            className="responsive-table-card",
            children=[
                dmc.Table(
                    highlightOnHover=True,
                    withTableBorder=False,
                    withColumnBorders=False,
                    children=[
                        dmc.TableThead(
                            dmc.TableTr([
                                dmc.TableTh("Image"),
                                dmc.TableTh("Title"),
                                dmc.TableTh("Players"),
                                dmc.TableTh("Play Time"),
                                dmc.TableTh("BGG Rating"),
                                dmc.TableTh("Status"),
                                dmc.TableTh("", style={"width": 100}),
                            ])
                        ),
                        dmc.TableTbody(rows),
                    ],
                )
            ],
        )
    else:
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
                        dmc.Box(
                            dmc.Text(
                                g["name"],
                                fw=700,
                                size="lg",
                                className="marquee-title",
                            ),
                            className="marquee-container",
                            mt="md",
                        ),
                        dmc.Group(
                            [
                                dmc.Group(
                                    create_status_badges(
                                        g.get("statuses", [])
                                    ),
                                    gap=5,
                                ),
                                dmc.Badge(
                                    f"{g['bgg_rating']:.1f}"
                                    if g.get("bgg_rating")
                                    else "N/A",
                                    color="yellow",
                                    variant="light",
                                ),
                            ],
                            justify="space-between",
                            mt="xs",
                            mb="xs",
                            wrap="nowrap",
                        ),
                        dmc.Text(
                            (
                                f"{g['min_players']}"
                                + (
                                    f"-{g['max_players']}"
                                    if g["min_players"] != g["max_players"]
                                    else ""
                                )
                                + " Players • "
                                + f"{g['min_play_time']}"
                                + (
                                    f"-{g['max_play_time']}"
                                    if g["min_play_time"] != g["max_play_time"]
                                    else ""
                                )
                                + " Min"
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
                id={"type": "game-card", "index": g["bgg_id"]},
                n_clicks=0,
                className="game-card-hover",
            )
            for g in page_games
        ]
        content = dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "lg": 4, "xl": 5},
            spacing="lg",
            children=cards,
        )

    pagination_style = {"display": "none"} if len(filtered) <= p_size else {}

    return (
        content,
        False,
        pagination_style,
    )


@callback(
    Output("layout-view-store", "data", allow_duplicate=True),
    Input("collection-view-toggle", "value"),
    prevent_initial_call=True,
)
def save_toggle_preference(value: str) -> str:
    """Save the view preference when changed in the header."""
    return value


@callback(
    Output("collection-view-toggle", "value"),
    Input("layout-view-store", "data"),
)
def sync_toggle_value(layout_view: str | None) -> str:
    """Initialize/sync the view toggle from local storage."""
    return layout_view or "grid"


@callback(
    Output("export-pdf-btn", "loading"),
    Output("collection-notification-container", "children"),
    Output("pdf-generation-trigger-store", "data"),
    Input("export-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)
def initiate_pdf_export(
    n_clicks: int | None,
) -> tuple[bool, dmc.Notification, dict[str, Any]] | NoUpdate:
    """Instantly show loading feedback and trigger the secondary PDF generation callback."""
    if not n_clicks:
        return no_update

    notification = dmc.Notification(
        id="pdf-export-notification",
        title="Generating PDF...",
        message="Compiling your board game catalog. This may take a few moments...",
        loading=True,
        autoClose=False,
        color="blue",
        action="show",
    )
    return True, notification, {"n_clicks": n_clicks}


@callback(
    Output("export-pdf-btn", "loading", allow_duplicate=True),
    Output(
        "collection-notification-container", "children", allow_duplicate=True
    ),
    Input("pdf-generation-trigger-store", "data"),
    State("filtered-collection-store", "data"),
    State("active-user-store", "data"),
    prevent_initial_call=True,
)
def process_pdf_generation(
    trigger_data: dict[str, Any] | None,
    filtered_games: list[dict[str, Any]] | None,
    active_user: str | None,
) -> tuple[bool, dmc.Notification] | NoUpdate:
    """Generate the catalog PDF, save it in the assets directory, and show a download link."""
    if not trigger_data:
        return no_update

    username = active_user or "guest"
    bgg_ids = []
    if filtered_games:
        bgg_ids = [g["bgg_id"] for g in filtered_games if "bgg_id" in g]

    buffer = io.BytesIO()
    with Session(engine) as session:
        if bgg_ids:
            games = session.exec(
                select(Game).where(Game.bgg_id.in_(bgg_ids))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
            ).all()
            game_ids = [g.id for g in games]
        else:
            game_ids = []

        from util.pdf_generator import generate_catalog_pdf

        generate_catalog_pdf(session, game_ids, buffer, username=username)

    # Save generated PDF to static exports cache

    export_dir = Path(tempfile.gettempdir()) / "spielpendium_exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{username}_board_game_catalog.pdf"
    file_path = export_dir / filename
    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())
    buffer.close()

    import gc

    gc.collect()

    download_url = f"/download/pdf/{filename}"

    notification = dmc.Notification(
        id="pdf-export-notification",
        title="PDF Export Ready",
        message=html.Span([
            "Your board game catalog is ",
            html.A(
                "ready",
                id="pdf-download-link",
                href=download_url,
                download=filename,
                style={
                    "cursor": "pointer",
                    "textDecoration": "underline",
                    "color": "var(--mantine-color-anchor)",
                },
            ),
            "!",
        ]),
        autoClose=False,
        color="green",
        icon=DashIconify(icon="tabler:check"),
        action="update",
        loading=False,
    )
    return False, notification


@callback(
    Output(
        "collection-notification-container", "children", allow_duplicate=True
    ),
    Input("pdf-download-link", "n_clicks"),
    prevent_initial_call=True,
)
def dismiss_pdf_notification(n_clicks: int | None) -> Any:
    """Clear the notification once the user clicks the download link."""
    if n_clicks:
        return None
    return no_update
