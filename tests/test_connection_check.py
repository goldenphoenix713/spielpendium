from __future__ import annotations

import email.message
import urllib.error
from unittest.mock import MagicMock, patch

import requests

from api.connection_check import (
    ConnectionStatus,
    bgg_api_is_up,
    bgg_is_up,
    get_connection_status,
)

# ---------------------------------------------------------------------------
# ConnectionStatus.__repr__ / __str__
# ---------------------------------------------------------------------------


def test_connection_status_repr() -> None:
    assert repr(ConnectionStatus.CONNECTION_OK) == "Connection Ok"
    assert repr(ConnectionStatus.BOARDGAMEGEEK_DOWN) == "Boardgamegeek Down"
    assert (
        repr(ConnectionStatus.BOARDGAMEGEEK_API_DOWN)
        == "Boardgamegeek Api Down"
    )


def test_connection_status_str_equals_repr() -> None:
    for status in ConnectionStatus:
        assert str(status) == repr(status)


# ---------------------------------------------------------------------------
# bgg_is_up
# ---------------------------------------------------------------------------


def test_bgg_is_up_returns_true_on_200() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch(
        "api.connection_check.requests.head", return_value=mock_response
    ):
        assert bgg_is_up() is True


def test_bgg_is_up_returns_false_on_http_error() -> None:
    with patch(
        "api.connection_check.requests.head",
        side_effect=requests.exceptions.HTTPError,
    ):
        assert bgg_is_up() is False


def test_bgg_is_up_returns_false_on_connection_error() -> None:
    with patch(
        "api.connection_check.requests.head",
        side_effect=requests.exceptions.ConnectionError,
    ):
        assert bgg_is_up() is False


def test_bgg_is_up_returns_false_when_raise_for_status_raises() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError

    with patch(
        "api.connection_check.requests.head", return_value=mock_response
    ):
        assert bgg_is_up() is False


# ---------------------------------------------------------------------------
# bgg_api_is_up
# ---------------------------------------------------------------------------


def test_bgg_api_is_up_returns_true_on_success() -> None:
    with patch(
        "api.connection_check.search_bgg", return_value={"results": []}
    ):
        assert bgg_api_is_up() is True


def test_bgg_api_is_up_returns_false_on_http_error() -> None:
    with patch(
        "api.connection_check.search_bgg",
        side_effect=urllib.error.HTTPError(
            "",
            503,
            "Service Unavailable",
            email.message.Message(),
            None,
        ),
    ):
        assert bgg_api_is_up() is False


# ---------------------------------------------------------------------------
# get_connection_status
# ---------------------------------------------------------------------------


def test_get_connection_status_ok() -> None:
    with (
        patch("api.connection_check.bgg_is_up", return_value=True),
        patch("api.connection_check.bgg_api_is_up", return_value=True),
    ):
        assert get_connection_status() == ConnectionStatus.CONNECTION_OK


def test_get_connection_status_bgg_down() -> None:
    with patch("api.connection_check.bgg_is_up", return_value=False):
        assert get_connection_status() == ConnectionStatus.BOARDGAMEGEEK_DOWN


def test_get_connection_status_api_down() -> None:
    with (
        patch("api.connection_check.bgg_is_up", return_value=True),
        patch("api.connection_check.bgg_api_is_up", return_value=False),
    ):
        assert (
            get_connection_status() == ConnectionStatus.BOARDGAMEGEEK_API_DOWN
        )
