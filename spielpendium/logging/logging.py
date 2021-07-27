import logging
import functools

_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_LEVELS = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}


def set_log_level(level: str):
    """Decorator for logging

    :param level: The logging level.
    :return: The decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def set_logging(*args, **kwargs):
            # Set the logger name to the function's module
            # and set the logging level.
            logger = get_logger(func.__module__, level=level)

            # Add the logger to the kwargs
            kwargs['logger'] = logger

            # Return the function
            return func(*args, **kwargs)
        return set_logging
    return decorator


def set_logging_config(filename: str, level: str = 'info'):
    """Sets up the logging configuration.

    :param filename: The filename of the log path.
    :param level: The logging level. Defaults to 'info'.
    """

    logging.basicConfig(filename=filename, format=_FORMAT, level=_LEVELS[level.lower()])


def get_logger(name: str, level: str = 'info') -> logging.Logger:
    """
    Sets up a logger to use in other parts of the code, ensuring consistent

    :param name: The name of the logger.
    :param level: The logging level. Defaults to 'info'
    :return: The logger object
    """

    logger = logging.getLogger(name)
    logger.setLevel(_LEVELS[level.lower()])

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FORMAT)

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
