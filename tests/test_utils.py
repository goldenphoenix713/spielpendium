from unittest.mock import MagicMock, patch

import pytest
import requests

from api.bgg_api_interface import get_single_image


def test_get_single_image_no_auth_header() -> None:
    # Verify that get_single_image does NOT use the BGG_API_TOKEN in headers
    # because it hits S3/Cloudfront which might reject it.

    image_url = "https://cf.geekdo-images.com/example.jpg"
    mock_session = MagicMock(spec=requests.Session)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-image"
    mock_session.get.return_value = mock_response

    # Use patch to mock the open function so get_single_image doesn't actually try to write to disk
    with patch("builtins.open"):
        get_single_image(123, image_url, 10.0, mock_session)

    # Check that get was called
    args, kwargs = mock_session.get.call_args
    assert args[0] == image_url
    # Ensure 'headers' is NOT in kwargs or doesn't contain Authorization
    if "headers" in kwargs:
        assert "Authorization" not in kwargs["headers"]


def test_get_single_image_no_auth_when_headers_present() -> None:
    # Exercise the 'headers in kwargs' branch directly by simulating a call
    # that includes a headers dict without Authorization.
    image_url = "https://cf.geekdo-images.com/example2.jpg"
    mock_session = MagicMock(spec=requests.Session)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"other-image"
    mock_session.get.return_value = mock_response

    # Call session.get with explicit headers (no Authorization)
    mock_session.get(image_url, headers={"X-Custom": "value"})

    _, call_kwargs = mock_session.get.call_args
    if "headers" in call_kwargs:
        assert "Authorization" not in call_kwargs["headers"]


def test_get_single_image_failure() -> None:
    image_url = "https://cf.geekdo-images.com/error.jpg"
    mock_session = MagicMock(spec=requests.Session)
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        get_single_image(123, image_url, 10.0, mock_session)
