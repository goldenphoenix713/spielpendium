import functools
import logging
from pathlib import Path

__all__ = ['log', 'logger']

LOGGING_LEVEL = logging.DEBUG

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

PATH = Path(__file__).parents[2].absolute()

print(PATH)


def create_logger():
    """
    Creates a logger object and returns it

    :return: The logger object.
    """
    logger_obj = logging.getLogger('Spielpendium')
    logger_obj.setLevel(LOGGING_LEVEL)

    # create the logging file handler
    file_handler = logging.FileHandler(rf"{PATH}/log/log.log")

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)

    # add handler to logger object
    logger_obj.addHandler(file_handler)
    return logger_obj


logger = create_logger()


def log(_logger: logging.Logger):

    def decorator(func):

        @functools.wraps(func)
        def inner(*args, **kwargs):

            # noinspection PyBroadException
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # log the exception
                logger.error(str(e))

                raise e

        return inner
    return decorator

