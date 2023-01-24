import logging

from ichrisbirch import settings

logger = logging.getLogger(__name__)

formatter = logging.Formatter(settings.logging.LOG_FORMAT)

console_log = logging.StreamHandler()
console_log.setFormatter(formatter)

file_log = logging.FileHandler(filename=settings.logging.LOG_PATH)
file_log.setFormatter(formatter)

logger.addHandler(console_log)
logger.addHandler(file_log)

logger.setLevel(settings.logging.LOG_LEVEL)
logger.debug(f'Log Location: {settings.logging.LOG_PATH}')

# quiet matplotlib noisy output when in debug mode
logging.getLogger('matplotlib').setLevel(logging.INFO)
