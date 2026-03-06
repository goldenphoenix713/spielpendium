from unittest.mock import MagicMock

import pytest
import requests

from api.bgg_api_interface import get_single_image
from util.images import get_b64_image


def test_get_b64_image() -> None:
    assert get_b64_image(None) == ""
    assert get_b64_image(b"") == ""

    test_bytes = b"hello"
    # base64(b"hello") -> aGVsbG8=
    expected = "data:image/jpeg;base64,aGVsbG8="
    assert get_b64_image(test_bytes) == expected


def test_get_single_image_no_auth_header() -> None:
    # Verify that get_single_image does NOT use the BGG_API_TOKEN in headers
    # because it hits S3/Cloudfront which might reject it.

    image_url = "https://cf.geekdo-images.com/example.jpg"
    mock_session = MagicMock(spec=requests.Session)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-image"
    mock_session.get.return_value = mock_response

    get_single_image(image_url, 10.0, mock_session)

    # Check that get was called
    args, kwargs = mock_session.get.call_args
    assert args[0] == image_url
    # Ensure 'headers' is NOT in kwargs or doesn't contain Authorization
    if "headers" in kwargs:
        assert "Authorization" not in kwargs["headers"]


def test_get_single_image_failure() -> None:
    image_url = "https://cf.geekdo-images.com/error.jpg"
    mock_session = MagicMock(spec=requests.Session)
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        get_single_image(image_url, 10.0, mock_session)
