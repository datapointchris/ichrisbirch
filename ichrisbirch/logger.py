import logging
import logging.config
import os
import platform


class No304StatusFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return '304 -' not in record.getMessage()


LOG_FORMAT = '[%(levelname)s] %(asctime)s %(name)s:%(funcName)s:%(lineno)d | %(message)s'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

logging_config = {
    'version': 1,
    'filters': {
        'no_304_status': {
            '()': No304StatusFilter,
        },
    },
    'formatters': {
        'standard': {
            'format': LOG_FORMAT,
            'datefmt': DATE_FORMAT,
        },
        'json': {
            'format': LOG_FORMAT,
            'datefmt': DATE_FORMAT,
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
            'filters': ['no_304_status'],
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'stream': 'ext://sys.stderr',
            'filters': ['no_304_status'],
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': '/var/log/ichrisbirch/pylogger.log',
            'mode': 'a',
            'filters': ['no_304_status'],
        },
        'json': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/var/log/ichrisbirch/pylogger.json',
            'mode': 'a',
            'filters': ['no_304_status'],
        },
    },
    'loggers': {
        '': {'level': 'DEBUG', 'handlers': ['stdout', 'stderr', 'file', 'json']},
        'apscheduler': {'level': 'WARNING'},
        'boto3': {'level': 'INFO'},
        'botocore': {'level': 'INFO'},
        'fsevents': {'level': 'INFO'},
        'httpcore': {'level': 'INFO'},
        'httpx': {'level': 'INFO'},
        'matplotlib': {'level': 'INFO'},
        's3transfer': {'level': 'INFO'},
        'urllib3': {'level': 'INFO'},
    },
}


def initialize_logging():
    github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    development = os.environ.get('ENVIRONMENT') == 'development'
    mac_os = platform.system() == 'Darwin'

    # Don't log to file in GitHub Actions
    if github_actions:
        del logging_config['handlers']['file']
        del logging_config['handlers']['json']
        logging_config['loggers']['']['handlers'] = ['stdout', 'stderr']

    # Don't log to stdout or stderr when developing or on macos
    # use the logs and running app and api in debug mode instead
    if development or mac_os:
        del logging_config['handlers']['stdout']
        del logging_config['handlers']['stderr']
        logging_config['loggers']['']['handlers'] = ['file', 'json']

    # Change log location on MacOS
    if mac_os:
        logging_config['handlers']['file']['filename'] = '/usr/local/var/log/ichrisbirch/pylogger.log'
        logging_config['handlers']['json']['filename'] = '/usr/local/var/log/ichrisbirch/pylogger.json'

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger()
    logger.info('Initialized logging')
    return logger
