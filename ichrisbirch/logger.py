"""Structlog configuration for the entire project."""

import functools
import logging
import os
import sys

import structlog
from structlog.processors import CallsiteParameter
from structlog.processors import CallsiteParameterAdder

LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')


def configure_structlog():
    """Configure structlog with appropriate processors.

    In testing mode, uses stdlib logging to integrate with pytest's caplog.
    In other environments, uses PrintLoggerFactory for direct output.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='%Y-%m-%dT%H:%M:%SZ'),
        CallsiteParameterAdder(
            {
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            }
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if ENVIRONMENT == 'testing':
        # Use stdlib logging for pytest caplog integration
        processors = shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        # Configure stdlib root logger for structlog output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=False, pad_level=True),
            )
        )
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, LOG_LEVEL))
    else:
        # Use PrintLoggerFactory for non-test environments
        if LOG_FORMAT == 'json':
            processors = shared_processors + [structlog.processors.JSONRenderer()]
        else:
            processors = shared_processors + [
                structlog.dev.ConsoleRenderer(
                    colors=sys.stdout.isatty(),
                    pad_level=True,
                )
            ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, LOG_LEVEL)),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def configure_stdlib_logging():
    """Suppress noisy third-party loggers."""
    third_party_levels = {
        'apscheduler': logging.WARNING,
        'asyncio': logging.INFO,
        'boto3': logging.INFO,
        'botocore': logging.INFO,
        'faker': logging.INFO,
        'fsevents': logging.INFO,
        'httpcore': logging.INFO,
        'httpx': logging.WARNING,
        'matplotlib': logging.INFO,
        'multipart.multipart': logging.INFO,
        'openai': logging.INFO,
        'python_multipart': logging.INFO,
        's3transfer': logging.INFO,
        'sqlalchemy_json': logging.INFO,
        'tzlocal': logging.INFO,
        'urllib3': logging.INFO,
        'watchdog': logging.INFO,
        'werkzeug': logging.WARNING,
    }
    for name, level in third_party_levels.items():
        logging.getLogger(name).setLevel(level)


@functools.lru_cache(maxsize=1)
def initialize_logging():
    """Initialize logging for the application."""
    configure_stdlib_logging()
    configure_structlog()
    logger = structlog.get_logger()
    logger.info('logging_initialized')
    return logger
