from unittest.mock import MagicMock, patch

from api.bgg_api.images import get_images, get_single_image


@patch("api.bgg_api.images.IMAGE_DIR")
def test_get_single_image_already_exists(mock_image_dir: MagicMock) -> None:
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_size = 100
    mock_image_dir.__truediv__.return_value = mock_path

    filename = get_single_image(
        123, "http://example.com/123.jpg", 10.0, MagicMock()
    )
    assert filename == "123.jpg"


@patch("api.bgg_api.images.get_single_image")
@patch("api.bgg_api.images.IMAGE_DIR")
def test_get_images_success(
    mock_image_dir: MagicMock, mock_get_single_image: MagicMock
) -> None:
    mock_path_existing = MagicMock()
    mock_path_existing.exists.return_value = True
    mock_path_existing.stat.return_value.st_size = 100

    mock_path_new = MagicMock()
    mock_path_new.exists.return_value = False

    def side_effect(name: str) -> MagicMock:
        if "111" in name:
            return mock_path_existing
        else:
            return mock_path_new

    mock_image_dir.__truediv__.side_effect = side_effect

    mock_get_single_image.return_value = "222.jpg"

    images_data = [(111, "http://url1"), (222, "http://url2")]

    result = get_images(images_data)

    assert result[111] == "111.jpg"
    assert result[222] == "222.jpg"
    mock_get_single_image.assert_called_once()


@patch("api.bgg_api.images.IMAGE_DIR")
def test_get_images_all_exist(mock_image_dir: MagicMock) -> None:
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_size = 100
    mock_image_dir.__truediv__.return_value = mock_path

    result = get_images((333, "http://url"))
    assert result[333] == "333.jpg"


@patch("api.bgg_api.images.get_single_image")
@patch("api.bgg_api.images.IMAGE_DIR")
def test_get_images_exception(
    mock_image_dir: MagicMock, mock_get_single_image: MagicMock
) -> None:
    mock_path = MagicMock()
    mock_path.exists.return_value = False
    mock_image_dir.__truediv__.return_value = mock_path

    mock_get_single_image.side_effect = Exception("Download failed")

    result = get_images([(444, "http://url")])
    assert result[444] is None
