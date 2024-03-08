import logging
import logging.config
import os
import platform


class No304StatusFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return '304 -' not in record.getMessage()


logging_config = {
    'version': 1,
    'filters': {
        'no_304_status': {
            '()': No304StatusFilter,
        },
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ',
        },
        'json': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ',
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
        'matplotlib': {'level': 'INFO'},
        'urllib3': {'level': 'INFO'},
        'apscheduler': {'level': 'WARNING'},
        'httpcore': {'level': 'INFO'},
        'httpx': {'level': 'INFO'},
        'fsevents': {'level': 'INFO'},
    },
}


def initialize_logging():
    # Don't log to file in GitHub Actions
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        del logging_config['handlers']['file']
        del logging_config['handlers']['json']
        logging_config['loggers']['']['handlers'] = ['stdout', 'stderr']

    # Change log location on MacOS
    if platform.system() == 'Darwin':
        logging_config['handlers']['file']['filename'] = '/usr/local/var/log/ichrisbirch/pylogger.log'
        logging_config['handlers']['json']['filename'] = '/usr/local/var/log/ichrisbirch/pylogger.json'

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger()
    logger.info('Initialized logging')
    return logger
