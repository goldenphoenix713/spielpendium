from unittest.mock import MagicMock, patch
from xml.parsers.expat import ExpatError

import pytest
import requests

from api.bgg_api.client import get_xml_info, search_bgg


@patch("api.bgg_api.client.bgg_session.get")
def test_get_xml_info_success(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<?xml version='1.0'?><data><item>1</item></data>"
    mock_get.return_value = mock_response

    result = get_xml_info("http://test.url")
    assert result == {"data": {"item": "1"}}
    mock_get.assert_called_once()


@patch("api.bgg_api.client.bgg_session.get")
@patch("api.bgg_api.client.time.sleep")
def test_get_xml_info_202_retry(
    mock_sleep: MagicMock, mock_get: MagicMock
) -> None:
    mock_response_202 = MagicMock()
    mock_response_202.status_code = 202

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.content = (
        b"<?xml version='1.0'?><data><item>2</item></data>"
    )

    # First call returns 202, second call returns 200
    mock_get.side_effect = [mock_response_202, mock_response_200]

    result = get_xml_info("http://test.url")
    assert result == {"data": {"item": "2"}}
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


@patch("api.bgg_api.client.bgg_session.get")
@patch("api.bgg_api.client.time.sleep")
def test_get_xml_info_429_retry(
    mock_sleep: MagicMock, mock_get: MagicMock
) -> None:
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.content = (
        b"<?xml version='1.0'?><data><item>3</item></data>"
    )

    # First call returns 429, second call returns 200
    mock_get.side_effect = [mock_response_429, mock_response_200]

    result = get_xml_info("http://test.url")
    assert result == {"data": {"item": "3"}}
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


@patch("api.bgg_api.client.bgg_session.get")
def test_get_xml_info_http_error(mock_get: MagicMock) -> None:
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500
    mock_response_500.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("Server Error")
    )
    mock_get.return_value = mock_response_500

    with pytest.raises(requests.exceptions.HTTPError):
        get_xml_info("http://test.url")


@patch("api.bgg_api.client.bgg_session.get")
@patch("api.bgg_api.client.time.sleep")
def test_get_xml_info_expat_error_retry(
    mock_sleep: MagicMock, mock_get: MagicMock
) -> None:
    mock_response_200_bad = MagicMock()
    mock_response_200_bad.status_code = 200
    mock_response_200_bad.content = b"Invalid XML"

    mock_response_200_good = MagicMock()
    mock_response_200_good.status_code = 200
    mock_response_200_good.content = b"<?xml version='1.0'?><data>good</data>"

    mock_get.side_effect = [mock_response_200_bad, mock_response_200_good]

    result = get_xml_info("http://test.url")
    assert result == {"data": "good"}
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


@patch("api.bgg_api.client.bgg_session.get")
@patch("api.bgg_api.client.MAX_API_CHECKS", 2)
@patch("api.bgg_api.client.time.sleep")
def test_get_xml_info_expat_error_max_retries(
    mock_sleep: MagicMock, mock_get: MagicMock
) -> None:
    mock_response_200_bad = MagicMock()
    mock_response_200_bad.status_code = 200
    mock_response_200_bad.content = b"Invalid XML"

    mock_get.return_value = mock_response_200_bad

    with pytest.raises(ExpatError):
        get_xml_info("http://test.url")
    assert mock_get.call_count == 2


@patch("api.bgg_api.client.get_xml_info")
def test_search_bgg(mock_get_xml_info: MagicMock) -> None:
    mock_get_xml_info.return_value = {"search": "results"}
    result = search_bgg("Catan", exact_flag=True)
    assert result == {"search": "results"}

    args, kwargs = mock_get_xml_info.call_args
    assert args[0].endswith("search")
    assert args[1]["query"] == "Catan"
    assert args[1]["exact"] == "1"
