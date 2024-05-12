"""Set up the logger for the entire project.

Loggers are set up for: app, api, scheduler, and third-party libraries.
The root logger is also set up to log to console and to a JSON file.
The app, api, and scheduler all log to their respectively named files,
while the ichrisbirch_file handler receives logs from everywhere, similar to the console.

NOTE: for some reason, setting the console handler to `log_level_in_brackets` formatter will affect
all of the other handlers when they are included in the same logger.

Example: the console handler logs in brackets.  If it is included in the app logger with the
app_file handler, the app_file handler will also log in brackets.

It appears that the custom formatter affects all of the handlers of that particular logger when set.
"""

import functools
import logging
import logging.config
import os
import platform


class No304StatusFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return '304 -' not in record.getMessage()


class LogLevelBracketFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        record.levelname = f'[{record.levelname}]'
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
    'log_level_in_brackets': {
        'format': BASIC_FORMAT,
        'datefmt': DATE_FORMAT,
        'style': '{',
        'class': 'ichrisbirch.logger.LogLevelBracketFormatter',
    },
}

HANDLERS = {
    'console': {
        'class': 'logging.StreamHandler',
        'level': 'DEBUG',
        'formatter': 'log_level_in_brackets',
        'stream': 'ext://sys.stdout',
        'filters': ['no_304_status'],
    },
    'ichrisbirch_file': {
        'class': 'logging.FileHandler',
        'level': 'DEBUG',
        'formatter': 'standard',
        'filename': f'{LOG_BASE_LOCATION}/ichrisbirch.log',
        'mode': 'a',
        'filters': ['no_304_status'],
    },
    'app_file': {
        'class': 'logging.FileHandler',
        'level': 'DEBUG',
        'formatter': 'standard',
        'filename': f'{LOG_BASE_LOCATION}/app.log',
        'mode': 'a',
        'filters': ['no_304_status'],
    },
    'api_file': {
        'class': 'logging.FileHandler',
        'level': 'DEBUG',
        'formatter': 'standard',
        'filename': f'{LOG_BASE_LOCATION}/api.log',
        'mode': 'a',
        'filters': ['no_304_status'],
    },
    'scheduler_file': {
        'class': 'logging.FileHandler',
        'level': 'DEBUG',
        'formatter': 'standard',
        'filename': f'{LOG_BASE_LOCATION}/scheduler.log',
        'mode': 'a',
        'filters': ['no_304_status'],
    },
    'json_file': {
        'class': 'logging.FileHandler',
        'level': 'DEBUG',
        'formatter': 'json',
        'filename': f'{LOG_BASE_LOCATION}/ichrisbirch.json',
        'mode': 'a',
        'filters': ['no_304_status'],
    },
}

LOGGERS = {
    'ichrisbirch': {
        'level': 'DEBUG',
        'handlers': ['console', 'ichrisbirch_file'],
        'propagate': False,
    },
    'app': {
        'level': 'DEBUG',
        'handlers': ['console', 'ichrisbirch_file', 'app_file'],
        'propagate': False,
    },
    'api': {
        'level': 'DEBUG',
        'handlers': ['console', 'ichrisbirch_file', 'api_file'],
        'propagate': False,
    },
    'scheduler': {
        'level': 'DEBUG',
        'handlers': ['console', 'ichrisbirch_file', 'scheduler_file'],
        'propagate': False,
    },
}

THIRD_PARTY_LOGGERS = {
    'apscheduler': {
        'level': 'WARNING',
        'handlers': ['console', 'ichrisbirch_file', 'scheduler_file'],
        'propagate': False,
    },
    'boto3': {'level': 'INFO'},
    'botocore': {'level': 'INFO'},
    'fsevents': {'level': 'INFO'},
    'httpcore': {'level': 'INFO'},
    'httpx': {'level': 'INFO'},
    'matplotlib': {'level': 'INFO'},
    's3transfer': {'level': 'INFO'},
    'urllib3': {'level': 'INFO'},
}

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': FILTERS,
    'formatters': FORMATTERS,
    'handlers': HANDLERS,
    'loggers': LOGGERS | THIRD_PARTY_LOGGERS,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'ichrisbirch_file', 'json_file'],
    },
}


@functools.lru_cache(maxsize=1)
def initialize_logging(config=LOGGING_CONFIG):
    github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    mac_os = platform.system() == 'Darwin'

    # Don't log to file in GitHub Actions
    # 1. Delete handlers so they don't try to create the log files
    # 2. Change loggers to only log to console
    # 3. Change root logger to only log to console
    if github_actions:
        temp = config['handlers'].copy()  # make a copy to avoid dict length change on iteration
        for handler in temp:
            if '_file' in handler:
                del config['handlers'][handler]
        for logger in config['loggers']:
            config['loggers'][logger]['handlers'] = ['console']
        config['root']['handlers'] = ['console']

    # Change log location on MacOS to /usr/local/var/log/ichrisbirch from /var/log/ichrisbirch
    if mac_os:
        for handler in config['handlers']:
            if '_file' in handler:
                config['handlers'][handler][
                    'filename'
                ] = f'{MACOS_LOG_BASE_LOCATION}/{handler.removesuffix('_file')}.log'

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
