from __future__ import annotations

from typing import TYPE_CHECKING

import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, register_page
from dash_iconify import DashIconify

from api.bgg_api.collection import get_user_game_collection

if TYPE_CHECKING:
    import plotly.graph_objects as go

register_page(__name__, path="/statistics")  # type: ignore[no-untyped-call]


def create_stat_card(
    title: str, value: str | int, icon: str, color: str
) -> dmc.Card:
    return dmc.Card(
        withBorder=True,
        shadow="sm",
        radius="md",
        p="lg",
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Text(
                                title,
                                size="xs",
                                c="dimmed",
                                fw=700,
                                tt="uppercase",
                            ),
                            dmc.Text(str(value), size="xl", fw=700),
                        ],
                    ),
                    dmc.ThemeIcon(
                        DashIconify(icon=icon, width=24),
                        size="xl",
                        radius="md",
                        variant="light",
                        color=color,
                    ),
                ],
            )
        ],
    )


def layout() -> dmc.Container:
    return dmc.Container(id="statistics-page-container", fluid=True)


@callback(
    Output("statistics-page-container", "children"),
    Input("active-user-store", "data"),
)
def render_statistics_content(username: str | None) -> dmc.Container:
    """Render the statistics content based on the active user."""
    if not username:
        return dmc.Container(
            dmc.Alert(
                "Please set a BoardGameGeek username in the home page first.",
                title="No User Set",
                color="blue",
                variant="filled",
                mt="xl",
            )
        )

    # We pass filters={} to get the full collection (not just owned)
    collection = get_user_game_collection(username, filters={})

    if not collection or not collection.items:
        return dmc.Container(
            dmc.Alert(
                f"No collection data found for user '{username}'. Please sync your collection first.",
                title="No Data",
                color="yellow",
                variant="filled",
                mt="xl",
            )
        )

    items = collection.items
    games = [it.game for it in items if it.game]

    # 1. Ownership Stats
    total_games = len(items)
    owned_count = sum(1 for it in items if "own" in it.statuses)
    wishlist_count = sum(
        1 for it in items if any(s.startswith("wishlist") for s in it.statuses)
    )

    avg_rating = 0.0
    rated_games = [g.bgg_rating for g in games if g.bgg_rating]
    if rated_games:
        avg_rating = sum(rated_games) / len(rated_games)

    # 2. Charts Data
    # Complexity
    weight_data = [g.complexity for g in games if g.complexity]
    weight_df = pd.DataFrame({"Complexity": weight_data})
    weight_df["Range"] = pd.cut(
        weight_df["Complexity"],
        bins=[1, 2, 3, 4, 5],
        labels=["1-2 (Light)", "2-3 (Medium)", "3-4 (Heavy)", "4-5 (Expert)"],
        include_lowest=True,
    )
    weight_counts = (
        weight_df["Range"].value_counts().sort_index().reset_index()
    )
    weight_counts.columns = ["Range", "Count"]

    fig_weight = px.bar(
        weight_counts,
        x="Range",
        y="Count",
        title="Complexity Distribution",
        template="plotly_dark",
        color="Range",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )

    # Player Count
    player_counts: dict[str, int] = {str(i): 0 for i in range(1, 6)}
    player_counts["6+"] = 0
    for g in games:
        for p in range(g.min_players, g.max_players + 1):
            if p <= 5:
                player_counts[str(p)] += 1
            else:
                player_counts["6+"] += 1
                break

    player_df = pd.DataFrame(
        list(player_counts.items()), columns=["Players", "Count"]
    )
    fig_players = px.bar(
        player_df,
        x="Players",
        y="Count",
        title="Games by Player Count",
        template="plotly_dark",
        color="Players",
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )

    # Categories
    all_categories: list[str] = []
    for g in games:
        all_categories.extend([c.name for c in g.categories])

    cat_series = pd.Series(all_categories).value_counts().head(10)
    cat_df = cat_series.reset_index()
    cat_df.columns = ["Category", "Count"]

    fig_cats = px.bar(
        cat_df,
        y="Category",
        x="Count",
        orientation="h",
        title="Top 10 Categories",
        template="plotly_dark",
        color="Count",
        color_continuous_scale="Viridis",
    )
    fig_cats.update_layout(yaxis={"autorange": "reversed"})

    # Status Pie
    all_statuses: list[str] = []
    for it in items:
        # Map statuses to more human readable
        for s in it.statuses:
            if s == "own":
                all_statuses.append("Owned")
            elif s == "want":
                all_statuses.append("Want in Trade")
            elif s == "wanttobuy":
                all_statuses.append("Want to Buy")
            elif s == "wanttoplay":
                all_statuses.append("Want to Play")
            elif s.startswith("wishlist"):
                all_statuses.append("Wishlist")
            elif s == "preordered":
                all_statuses.append("Pre-ordered")

    status_series = pd.Series(all_statuses).value_counts()
    status_df = status_series.reset_index()
    status_df.columns = ["Status", "Count"]

    fig_status = px.pie(
        status_df,
        values="Count",
        names="Status",
        title="Collection Breakdown",
        template="plotly_dark",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )

    # Designers
    all_designers: list[str] = []
    for g in games:
        all_designers.extend([p.name for p in g.authors])
    des_df = pd.Series(all_designers).value_counts().head(10).reset_index()
    des_df.columns = ["Designer", "Count"]
    fig_designers = px.bar(
        des_df,
        y="Designer",
        x="Count",
        orientation="h",
        title="Top 10 Designers",
        template="plotly_dark",
        color="Count",
        color_continuous_scale="Reds",
    )
    fig_designers.update_layout(yaxis={"autorange": "reversed"})

    # Publishers
    all_publishers: list[str] = []
    for g in games:
        all_publishers.extend([p.name for p in g.publishers])
    pub_df = pd.Series(all_publishers).value_counts().head(10).reset_index()
    pub_df.columns = ["Publisher", "Count"]
    fig_pubs = px.bar(
        pub_df,
        y="Publisher",
        x="Count",
        orientation="h",
        title="Top 10 Publishers",
        template="plotly_dark",
        color="Count",
        color_continuous_scale="Blues",
    )
    fig_pubs.update_layout(yaxis={"autorange": "reversed"})

    # Custom chart styling to match Mantine Dark theme
    def style_fig(fig: go.Figure) -> None:
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#C1C2C5",
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
            title_font_size=16,
            title_x=0.5,
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#2C2E33")

    style_fig(fig_players)
    style_fig(fig_weight)
    style_fig(fig_status)
    style_fig(fig_cats)
    style_fig(fig_designers)
    style_fig(fig_pubs)

    fig_cats.update_layout(height=400)
    fig_status.update_layout(height=400)
    fig_designers.update_layout(height=400)
    fig_pubs.update_layout(height=400)

    return dmc.Container(
        size="lg",
        p="md",
        children=[
            dmc.Title("Collection Statistics", order=1, mb="xl"),
            dmc.SimpleGrid(
                cols={"base": 1, "sm": 2, "md": 4},
                spacing="lg",
                mb="xl",
                children=[
                    create_stat_card(
                        "Total Items",
                        total_games,
                        "game-icons:box-trap",
                        "blue",
                    ),
                    create_stat_card(
                        "Owned", owned_count, "game-icons:check-mark", "green"
                    ),
                    create_stat_card(
                        "Wishlist",
                        wishlist_count,
                        "game-icons:star-swirl",
                        "yellow",
                    ),
                    create_stat_card(
                        "Avg Rating",
                        f"{avg_rating:.2f}",
                        "game-icons:round-star",
                        "orange",
                    ),
                ],
            ),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="lg",
                mb="lg",
                children=[
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_players,
                                config={"displayModeBar": False},
                                style={"height": "350px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_weight,
                                config={"displayModeBar": False},
                                style={"height": "350px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                ],
            ),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="lg",
                mb="lg",
                children=[
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_status,
                                config={"displayModeBar": False},
                                style={"height": "400px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_cats,
                                config={"displayModeBar": False},
                                style={"height": "400px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                ],
            ),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="lg",
                children=[
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_designers,
                                config={"displayModeBar": False},
                                style={"height": "400px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                    dmc.Paper(
                        children=[
                            dcc.Graph(
                                figure=fig_pubs,
                                config={"displayModeBar": False},
                                style={"height": "400px"},
                            )
                        ],
                        withBorder=True,
                        p="md",
                        radius="md",
                    ),
                ],
            ),
        ],
    )
