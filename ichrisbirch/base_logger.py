import logging

from ichrisbirch import settings

logger = logging.getLogger(__name__)
log_file = f'{settings.logging.LOG_PATH}/pylogger.log'

formatter = logging.Formatter(settings.logging.LOG_FORMAT, settings.logging.LOG_DATE_FORMAT)

console_log = logging.StreamHandler()
console_log.setFormatter(formatter)

file_log = logging.FileHandler(filename=log_file)
file_log.setFormatter(formatter)

logger.addHandler(console_log)
logger.addHandler(file_log)

logger.setLevel(settings.logging.LOG_LEVEL)
logger.debug(f'Log Location: {log_file}')

# quiet matplotlib noisy output when in debug mode
logging.getLogger('matplotlib').setLevel(logging.INFO)
