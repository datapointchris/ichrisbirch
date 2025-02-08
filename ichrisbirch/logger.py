"""Set up the logger for the entire project.

Loggers are set up for: app, api, scheduler, and third-party libraries.
The root logger is also set up to log to console and to a JSON file.
The app, api, and scheduler all log to their respectively named files,
while the ichrisbirch_file handler receives logs from everywhere, similar to the console.

Awesome logging tutorial: https://www.youtube.com/watch?v=9L77QExPmI0
"""

import functools
import logging
import logging.config
import logging.handlers
import os
import platform


class No304StatusFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return '304 -' not in record.getMessage()


class SingleLineLogLevelBracketFormatter(logging.Formatter):
    """Add brackets around log level and remove all newlines."""

    def format(self, record: logging.LogRecord):
        if not record.levelname.startswith('['):
            record.levelname = f'[{record.levelname}]'
        # record.msg = record.msg.replace('\n', ' ').replace('\r', ' ')
        return logging.Formatter.format(self, record)


class ColoredLevelFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629

    NOT currently being used, this is here for reference only.
    """

    GRAY = '\x1b[38;21m'
    GREEN = '\x1b[38;5;40m'
    BLUE = '\x1b[38;5;39m'
    YELLOW = '\x1b[38;5;226m'
    RED = '\x1b[38;5;196m'
    BOLD_RED = '\x1b[31;1m'
    RESET = '\x1b[0m'

    FORMATS = {
        logging.DEBUG: GREEN,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record):
        color_for_level = self.FORMATS.get(record.levelno)
        colored_level_name = f'{color_for_level}[{record.levelname}]{self.RESET}'
        record.levelname = colored_level_name
        return logging.Formatter.format(self, record)


DETAILED_FORMAT = '{levelname:9} {asctime} {name}:{funcName}:{lineno} | {message}'
BASIC_FORMAT = '{levelname:9} {asctime} {name}: {message}'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

LOG_BASE_LOCATION = '/var/log/ichrisbirch'
MACOS_LOG_BASE_LOCATION = '/usr/local/var/log/ichrisbirch'

GLOBAL_LOG_LEVEL = 'DEBUG'

FILTERS = {
    'no_304_status': {
        '()': No304StatusFilter,
    },
}

FORMATTERS = {
    'standard': {
        'format': BASIC_FORMAT,
        'datefmt': DATE_FORMAT,
        'style': '{',
    },
    'json': {
        'format': BASIC_FORMAT,
        'datefmt': DATE_FORMAT,
        'style': '{',
        'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
    },
    'single_line_log_level_in_brackets': {
        'format': DETAILED_FORMAT,
        'datefmt': DATE_FORMAT,
        'style': '{',
        'class': 'ichrisbirch.logger.SingleLineLogLevelBracketFormatter',
    },
}

HANDLERS = {
    'console': {
        'formatter': 'single_line_log_level_in_brackets',
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
    },
    'ichrisbirch_file': {
        'formatter': 'single_line_log_level_in_brackets',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'filename': f'{LOG_BASE_LOCATION}/ichrisbirch.log',
    },
    'app_file': {
        'formatter': 'single_line_log_level_in_brackets',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'filename': f'{LOG_BASE_LOCATION}/app.log',
    },
    'api_file': {
        'formatter': 'single_line_log_level_in_brackets',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'filename': f'{LOG_BASE_LOCATION}/api.log',
    },
    'scheduler_file': {
        'formatter': 'single_line_log_level_in_brackets',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'filename': f'{LOG_BASE_LOCATION}/scheduler.log',
    },
    'json_file': {
        'formatter': 'json',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'filename': f'{LOG_BASE_LOCATION}/ichrisbirch.json',
    },
}


LOGGERS = {
    'root': {
        'level': GLOBAL_LOG_LEVEL,
        'handlers': ['console', 'ichrisbirch_file', 'json_file'],
        'filters': ['no_304_status'],
    },
    'ichrisbirch': {},
    'app': {'handlers': ['app_file']},
    'api': {'handlers': ['api_file']},
    'scheduler': {'handlers': ['scheduler_file']},
    'tests.conftest': {'level': 'INFO'},
}


# these are set to quiet down noisy libraries when debug is on
THIRD_PARTY_LOGGERS = {
    'apscheduler': {'level': 'WARNING', 'handlers': ['scheduler_file']},
    'boto3': {'level': 'INFO'},
    'botocore': {'level': 'INFO'},
    'faker': {'level': 'INFO'},
    'fsevents': {'level': 'INFO'},
    'httpcore': {'level': 'INFO'},
    'httpx': {'level': 'WARNING'},
    'matplotlib': {'level': 'INFO'},
    'multipart.multipart': {'level': 'INFO'},
    'openai': {'level': 'INFO'},
    'pytho_multipart': {'level': 'INFO'},
    's3transfer': {'level': 'INFO'},
    'tzlocal': {'level': 'INFO'},
    'urllib3': {'level': 'INFO'},
    'werkzeug': {'handlers': ['app_file'], 'filters': ['no_304_status']},
}

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': FILTERS,
    'formatters': FORMATTERS,
    'handlers': HANDLERS,
    'loggers': LOGGERS | THIRD_PARTY_LOGGERS,
}


@functools.lru_cache(maxsize=1)
def initialize_logging(config=LOGGING_CONFIG):
    github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    mac_os = platform.system() == 'Darwin'

    # Don't log to file in GitHub Actions
    # 1. Delete handlers so they don't try to create the log files
    # 2. Change loggers to only log to console
    if github_actions:
        temp = config['handlers'].copy()  # make a copy to avoid dict length change on iteration
        for handler in temp:
            if '_file' in handler:
                del config['handlers'][handler]
        for logger in config['loggers']:
            config['loggers'][logger]['handlers'] = ['console']

    # Change log location on MacOS to /usr/local/var/log/ichrisbirch from /var/log/ichrisbirch
    if mac_os:
        for handler in config['handlers']:
            if '_file' in handler:
                filename = f'{MACOS_LOG_BASE_LOCATION}/{handler.removesuffix('_file')}.log'
                config['handlers'][handler]['filename'] = filename

    logging.config.dictConfig(config)
    logger = logging.getLogger()
    logger.info('initialized logging')
    return logger


# Currently not using this, was possibly a way to use a decorator to setup logging
# instead of calling initialize_logging() in the project __init__.py
# but the imports were triggering first and messing up logger instantiation
def with_logging_setup(target_function):
    @functools.wraps(target_function)
    def wrapper(*args, **kwargs):
        initialize_logging()
        return target_function(*args, **kwargs)

    return wrapper
