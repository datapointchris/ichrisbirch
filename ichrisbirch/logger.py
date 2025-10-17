"""Set up the logger for the entire project.

Loggers are set up for: app, api, scheduler, and third-party libraries. The root logger is also set up to log to console and to a JSON file.
The app, api, and scheduler all log to their respectively named files, while the ichrisbirch_file handler receives logs from everywhere,
similar to the console.

Awesome logging tutorial:
https://www.youtube.com/watch?v=9L77QExPmI0
"""

import functools
import logging
import logging.config
import logging.handlers
import os


class No304StatusFilter(logging.Filter):
    """No longer used, instead app.middleware.RequestLoggingMiddleware is handling request logging and filtering."""

    def filter(self, record: logging.LogRecord):
        return '304 -' not in record.getMessage()


class EnhancedLogFormatter(logging.Formatter):
    """Enhanced formatter that strips package prefix, adds brackets around log level."""

    def format(self, record: logging.LogRecord):
        record.name.removeprefix('ichrisbirch.')
        # Add brackets around log level
        if not record.levelname.startswith('['):
            record.levelname = f'[{record.levelname}]'

        # Remove newlines
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

# LOG_BASE_LOCATION = os.environ['LOG_DIR']
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
    # 'json': {
    #     'format': BASIC_FORMAT,
    #     'datefmt': DATE_FORMAT,
    #     'style': '{',
    #     'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
    # },
    'enhanced': {
        'format': DETAILED_FORMAT,
        'datefmt': DATE_FORMAT,
        'style': '{',
        'class': 'ichrisbirch.logger.EnhancedLogFormatter',
    },
}

# Build handlers dynamically based on environment
HANDLERS: dict = {
    'stdout': {
        'formatter': 'enhanced',
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
    },
}

# Add file handler if LOG_FILE_PATH is set (for test environment persistent logging)
if log_file_path := os.environ.get('LOG_FILE_PATH'):
    HANDLERS['file'] = {
        'formatter': 'enhanced',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'backupCount': 3,
        'filename': log_file_path,
    }


LOGGERS = {
    'root': {
        'level': GLOBAL_LOG_LEVEL,
        'handlers': ['stdout'] + (['file'] if 'file' in HANDLERS else []),
    },
    'ichrisbirch': {},
    'tests.conftest': {'level': 'INFO'},
}


# these are set to quiet down noisy libraries when debug is on
THIRD_PARTY_LOGGERS = {
    'apscheduler': {'level': 'WARNING'},
    'asyncio': {'level': 'INFO'},
    'boto3': {'level': 'INFO'},
    'botocore': {'level': 'INFO'},
    'faker': {'level': 'INFO'},
    'fsevents': {'level': 'INFO'},
    'httpcore': {'level': 'INFO'},
    'httpx': {'level': 'WARNING'},
    'matplotlib': {'level': 'INFO'},
    'multipart.multipart': {'level': 'INFO'},
    'openai': {'level': 'INFO'},
    'python_multipart': {'level': 'INFO'},
    's3transfer': {'level': 'INFO'},
    'sqlalchemy_json': {'level': 'INFO'},
    'tzlocal': {'level': 'INFO'},
    'urllib3': {'level': 'INFO'},
    'watchdog': {'level': 'INFO'},
    'werkzeug': {'level': 'WARNING'},
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

    # Don't log to file in GitHub Actions
    # 1. Delete handlers so they don't try to create the log files
    # 2. Change loggers to only log to console
    if github_actions:
        temp = config['handlers'].copy()  # make a copy to avoid dict length change on iteration
        for handler in temp:
            if '_file' in handler:
                del config['handlers'][handler]
        for logger in config['loggers']:
            config['loggers'][logger]['handlers'] = ['stdout']

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
