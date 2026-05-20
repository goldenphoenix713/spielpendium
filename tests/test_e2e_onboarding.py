from __future__ import annotations

from unittest.mock import MagicMock, patch

import dash_mantine_components as dmc

with patch("dash.register_page"):
    from pages.collection import (
        filter_collection,
        load_collection_store,
        render_grid,
    )
    from pages.home import render_home_content
    from pages.settings import save_settings


def test_e2e_onboarding_flow():
    """Simulate the complete user onboarding E2E lifecycle.

    Steps:
      1. User lands on Home Page (unauthenticated/empty state).
      2. User adds a BGG account and saves configuration.
      3. Collection data is retrieved, filtered, and paginated.
      4. Games are successfully rendered in grid and list formats.
    """
    # Step 1: Verify Initial Onboarding Content on Home Page
    onboarding_layout = render_home_content(None)
    assert "Welcome to Spielpendium" in str(onboarding_layout)
    assert "Connect Collection" in str(onboarding_layout)

    # Step 2: Simulate User Connecting BGG Account & Saving Settings
    with patch("pages.settings.dash.ctx") as mock_ctx:
        mock_ctx.states_list = [
            [{"id": {"item": "theme"}}, {"id": {"item": "primary_color"}}]
        ]
        # Save a new BGG username profile
        res = save_settings(
            n_clicks=1,
            username="phoenix713",
            usernames=["phoenix713"],
            page_size=20,
            theme="dark",
            primary_color="blue",
            auto_refresh=True,
            layout_view="grid",
        )
        # Verify notifications and local store values returned
        assert isinstance(res[0], dmc.Notification)
        assert res[3] == "phoenix713"
        assert res[4] == ["phoenix713"]
        assert res[5] == "grid"
        assert res[6] is True
        assert res[7] == 20

    # Step 3: Simulate Ingested Games Loading into Collection Stores
    mock_collection = MagicMock()
    mock_item = MagicMock()
    mock_item.game.bgg_id = 999
    mock_item.game.name = "Terraforming Mars"
    mock_item.game.min_players = 1
    mock_item.game.max_players = 5
    mock_item.game.min_play_time = 90
    mock_item.game.max_play_time = 120
    mock_item.game.bgg_rating = 8.4
    mock_item.game.image_path = "tf_mars.jpg"
    mock_item.statuses = ["own", "wanttoplay"]
    mock_collection.items = [mock_item]

    with patch(
        "pages.collection.get_user_game_collection",
        return_value=mock_collection,
    ):
        games = load_collection_store(sync_trigger=1, active_user="phoenix713")
        assert len(games) == 1
        assert games[0]["name"] == "Terraforming Mars"
        assert games[0]["bgg_id"] == 999

    # Step 4: Apply Real-time Filters and Pagination
    filters = {
        "name": "Terraform",
        "players": [3, 3],
        "ownership": ["own"],
    }
    filtered, count_text, active_page, total_pages = filter_collection(
        games, filters, page_size=20
    )
    assert len(filtered) == 1
    assert "1 game" in count_text
    assert total_pages == 1

    # Step 5: Render Layout in Grid View (Default)
    grid_view_layout, loading, pagination_style = render_grid(
        filtered=filtered,
        page=1,
        active_user="phoenix713",
        view_mode="grid",
        page_size=20,
        layout_view="grid",
    )
    assert isinstance(grid_view_layout, dmc.SimpleGrid)
    assert loading is False

    # Step 6: Render Layout in List/Table View
    list_view_layout, loading, pagination_style = render_grid(
        filtered=filtered,
        page=1,
        active_user="phoenix713",
        view_mode="list",
        page_size=20,
        layout_view="grid",
    )
    assert isinstance(list_view_layout, dmc.Card)
    # Ensure it contains a Mantine Table structure
    assert isinstance(list_view_layout.children[0], dmc.Table)
