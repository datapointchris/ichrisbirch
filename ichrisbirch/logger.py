import logging
import logging.config

config = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ',
        },
        'json': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
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
    },
}


def initialize_logging():
    logging.config.dictConfig(config)
    logger = logging.getLogger()
    logger.info('Initialized logging')
    return logger
