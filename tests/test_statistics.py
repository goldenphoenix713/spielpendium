from __future__ import annotations

from unittest.mock import MagicMock, patch

with patch("dash.register_page"):
    from pages.statistics import layout, render_statistics_content


def test_statistics_layout():
    # Test the outer layout
    res = layout()
    assert getattr(res, "id", None) == "statistics-page-container"


def test_render_statistics_content():
    # Test no user
    res = render_statistics_content(None)
    assert "No User Set" in str(res)

    # Test with user but no collection
    with patch("pages.statistics.get_user_game_collection") as mock_get_coll:
        mock_get_coll.return_value = None
        res = render_statistics_content("testuser")
        assert "No Data" in str(res)

        # Mock non-empty collection (minimal structure)
        mock_coll = MagicMock()
        mock_coll.items = []
        mock_get_coll.return_value = mock_coll
        res = render_statistics_content("testuser")
        assert "No Data" in str(res)


def test_render_statistics_content_with_data():
    """Test statistics rendering with mocked game data."""
    with patch("pages.statistics.get_user_game_collection") as mock_get_coll:
        # Create a mock game with all fields needed for stats
        mock_game_obj = MagicMock()
        mock_game_obj.name = "Test Game"
        mock_game_obj.complexity = 3.0
        mock_game_obj.min_players = 1
        mock_game_obj.max_players = 4
        mock_game_obj.bgg_rating = 8.5
        mock_game_obj.release_year = 2020
        mock_game_obj.min_play_time = 30
        mock_game_obj.max_play_time = 60

        # Categories
        cat_link = MagicMock()
        cat_link.category.name = "Strategy"
        mock_game_obj.categories = [cat_link]

        # Authors
        author_link = MagicMock()
        author_link.author.name = "John Doe"
        mock_game_obj.authors = [author_link.author]

        # Publishers
        pub_link = MagicMock()
        pub_link.publisher.name = "Cool Games"
        mock_game_obj.publishers = [pub_link.publisher]

        mock_item = MagicMock()
        mock_item.game = mock_game_obj
        mock_item.ownership_status = "own"
        mock_item.statuses = ["own"]

        mock_coll = MagicMock()
        mock_coll.items = [mock_item]
        mock_get_coll.return_value = mock_coll

        res = render_statistics_content("testuser")

        # Check for key sections in the dashboard
        res_str = str(res)
        assert "Collection Statistics" in res_str
        assert "Total Items" in res_str
        assert "Complexity Distribution" in res_str
        assert "Games by Player Count" in res_str
        assert "Collection Breakdown" in res_str
        assert "Top 10 Categories" in res_str
