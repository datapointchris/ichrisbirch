"""Structlog configuration - simple, consistent, stdout only.

All logs go to stdout. Docker handles persistence via its logging driver.
Configuration is controlled by three environment variables:
- LOG_FORMAT: 'console' (default) or 'json'
- LOG_LEVEL: 'DEBUG' (default), 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
- LOG_COLORS: 'auto' (default), 'true', 'false'

Note: 304 redirect filtering is handled by app.middleware.RequestLoggingMiddleware,
not by the logging configuration.
"""

import functools
import logging
import os
import sys

import structlog
from structlog.processors import CallsiteParameter
from structlog.processors import CallsiteParameterAdder

LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
LOG_COLORS = os.environ.get('LOG_COLORS', 'auto')


def _use_colors() -> bool:
    """Determine if colors should be used in console output.

    LOG_COLORS env var controls this:
    - 'true': Force colors on (useful in Docker where TTY detection fails)
    - 'false': Force colors off
    - 'auto': Use TTY detection
    """
    if LOG_COLORS == 'true':
        return True
    if LOG_COLORS == 'false':
        return False
    return sys.stdout.isatty()


def configure_structlog():
    """Configure structlog - all output goes to stdout."""
    processors = [
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

    if LOG_FORMAT == 'json':
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=_use_colors(),
                pad_level=True,
            )
        )

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
