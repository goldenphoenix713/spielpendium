import logging
import os
import functools

from spielpendium.constants import (PROGRAM_NAME, LOG_DIR as _LOG_DIR,
                                    LOG_FILE as _LOG_FILE)

__author__ = 'Eduardo Ruiz'

__all__ = ['log', 'logger']

# Define some constants
_LOG_FORMAT = '[%(asctime)s %(levelname)s] %(message)s'


def _create_logger() -> logging.Logger:
    """
    Creates a logging object and returns it.

    :return: The logging object.
    """
    # Set up the logger and set its level
    logger_obj = logging.getLogger(PROGRAM_NAME)
    logger_obj.setLevel(logging.DEBUG)

    # Configure the path to the log file
    if not os.path.isdir(_LOG_DIR):
        os.mkdir(_LOG_DIR)

    # If we're debugging, start with a fresh log file each time
    if os.path.isfile(_LOG_FILE) and logger_obj.level == logging.DEBUG:
        os.remove(_LOG_FILE)

    # Create the logging file handler
    fh = logging.FileHandler(_LOG_FILE)

    # Create the logging formatter
    formatter = logging.Formatter(_LOG_FORMAT)

    # Set the formatter of the handler
    fh.setFormatter(formatter)

    # Add handler to logger object
    logger_obj.addHandler(fh)
    return logger_obj


# Create the logger object to use throughout the program
logger = _create_logger()


def log(_logger: logging.Logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    :param _logger: The logging object
    """

    def decorator(func):
        # Get the full path to the function (packages as modules) for debugging
        func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger.debug(f'Entering {func_name}.')
            try:
                # Try to run the function
                ret = func(*args, **kwargs)
            except Exception as e:
                # Log the exception
                err = (f'An exception of type {type(e).__name__} occurred in'
                       f' {func_name}.\nFunction arguments:\n'
                       f'    args={args}\n'
                       f'    kwargs={kwargs}')
                _logger.exception(err)

                # Re-raise the exception
                raise e
            else:
                _logger.debug(f'Exiting {func_name}.')

            return ret

        return wrapper

    return decorator
