import logging

from ichrisbirch.config import get_settings

settings = get_settings()


def init():
    """Initialize the base logger"""
    logger = logging.getLogger(__name__)
    log_file = f'{settings.logging.log_dir}/pylogger.log'

    formatter = logging.Formatter(settings.logging.log_format, settings.logging.log_date_format)

    console_log = logging.StreamHandler()
    console_log.setFormatter(formatter)

    file_log = logging.FileHandler(filename=log_file)
    file_log.setFormatter(formatter)

    logger.addHandler(console_log)
    logger.addHandler(file_log)

    logger.setLevel(settings.logging.log_level)
    logger.debug(f'Log Location: {log_file}')

    # quiet matplotlib noisy output when in debug mode
    if settings.logging.log_level == logging.DEBUG:
        logging.getLogger('matplotlib').setLevel(logging.INFO)
