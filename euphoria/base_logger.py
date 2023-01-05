import logging

from euphoria import settings

logger = logging.getLogger()

formatter = logging.Formatter(settings.logging.LOG_FORMAT)

console_log = logging.StreamHandler()
console_log.setFormatter(formatter)

file_log = logging.FileHandler(filename=settings.logging.LOG_PATH)
file_log.setFormatter(formatter)

logger.addHandler(console_log)
logger.addHandler(file_log)

logger.setLevel(settings.logging.LOG_LEVEL)
logger.debug(f'Log Location: {settings.logging.LOG_PATH}')

logging.getLogger('matplotlib').setLevel(logging.INFO)