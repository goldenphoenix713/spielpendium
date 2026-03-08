from unittest.mock import patch

from util.log import set_up_logger


def test_set_up_logger_debug_true() -> None:
    with (
        patch("util.log.DEBUG", True),
        patch("util.log.logger") as mock_logger,
    ):
        set_up_logger()
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2
        # First add is stderr
        assert mock_logger.add.call_args_list[0][1]["level"] == "DEBUG"
        # Second add is log file
        assert mock_logger.add.call_args_list[1][1]["level"] == "DEBUG"


def test_set_up_logger_debug_false() -> None:
    with (
        patch("util.log.DEBUG", False),
        patch("util.log.logger") as mock_logger,
    ):
        set_up_logger()
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2
        # First add is stderr
        assert mock_logger.add.call_args_list[0][1]["level"] == "INFO"
        # Second add is log file
        assert mock_logger.add.call_args_list[1][1]["level"] == "INFO"
