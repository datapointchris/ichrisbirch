import logging
import logging.config
import os
import platform

logging_config = {
    'version': 1,
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
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': '/var/log/ichrisbirch/pylogger.log',
            'mode': 'a',
        },
        'json': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/var/log/ichrisbirch/pylogger.json',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {'level': 'DEBUG', 'handlers': ['stdout', 'stderr', 'file', 'json']},
        'matplotlib': {'level': 'INFO'},
        'urllib3': {'level': 'INFO'},
        'apscheduler': {'level': 'WARNING'},
        'httpcore': {'level': 'INFO'},
        'httpx': {'level': 'INFO'},
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
