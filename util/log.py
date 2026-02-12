from __future__ import annotations

import functools
import logging
import os
from typing import TYPE_CHECKING

from config import APP_NAME, DEBUG, LOG_DIR, LOG_FILE, LOG_FORMAT

if TYPE_CHECKING:
    from collections.abc import Callable

__author__ = "Eduardo Ruiz"

__all__ = ["log", "logger"]


def _create_logger() -> logging.Logger:
    """
    Creates a logging object and returns it.

    :return: The logging object.
    """
    # Set up the logger and set its level
    logger_obj = logging.getLogger(APP_NAME)
    logger_obj.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Configure the path to the log file
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)

    # If we're debugging, start with a fresh log file each time
    if os.path.isfile(LOG_FILE) and logger_obj.level == logging.DEBUG:
        os.remove(LOG_FILE)

    # Create the logging file handler
    fh = logging.FileHandler(LOG_FILE)

    # Create the logging formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Set the formatter of the handler
    fh.setFormatter(formatter)

    # Add handler to logger object
    logger_obj.addHandler(fh)
    return logger_obj


# Create the logger object to use throughout the program
logger = _create_logger()


def log(_logger: logging.Logger) -> Callable:  # type: ignore[type-arg]
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    :param _logger: The logging object
    """

    def decorator(func: Callable) -> Callable:  # type: ignore[type-arg]
        # Get the full path to the function (packages as modules) for debugging
        func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            _logger.debug(f"Entering {func_name}.")
            try:
                # Try to run the function
                ret = func(*args, **kwargs)
            except Exception as e:
                # Log the exception
                err = (
                    f"An exception of type {type(e).__name__} occurred in"
                    f" {func_name}.\nFunction arguments:\n"
                    f"    args={args}\n"
                    f"    kwargs={kwargs}"
                )
                _logger.exception(err)

                # Re-raise the exception
                raise e
            else:
                _logger.debug(f"Exiting {func_name}.")

            return ret

        return wrapper

    return decorator
