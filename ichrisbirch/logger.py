"""Structlog configuration with optional file logging.

All logs go to stdout. Optionally also writes to a file for admin UI and persistence.
Configuration is controlled by environment variables:
- LOG_FORMAT: 'console' (default) or 'json'
- LOG_LEVEL: 'DEBUG' (default), 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
- LOG_COLORS: 'auto' (default), 'true', 'false'
- LOG_FILE: Path to log file (optional, enables file logging if set and directory exists)

Note: 304 redirect filtering is handled by app.middleware.RequestLoggingMiddleware,
not by the logging configuration.
"""

import functools
import logging
import os
import sys
from pathlib import Path

import structlog
from structlog.processors import CallsiteParameter
from structlog.processors import CallsiteParameterAdder

LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
LOG_COLORS = os.environ.get('LOG_COLORS', 'auto')
LOG_FILE = os.environ.get('LOG_FILE', '')
LOG_DIR = os.environ.get('LOG_DIR', '/var/log/ichrisbirch')


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


def _setup_file_handler() -> logging.Handler | None:
    """Set up rotating file handler if LOG_FILE is configured and directory exists.

    Uses RotatingFileHandler to prevent unbounded log growth:
    - Max 25MB per file
    - Keeps 5 backup files (app.log.1, app.log.2, etc.)
    - Total max ~150MB per service
    """
    if not LOG_FILE:
        return None

    log_path = Path(LOG_FILE)
    if not log_path.parent.exists():
        return None

    try:
        from logging.handlers import RotatingFileHandler

        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=25 * 1024 * 1024,  # 25MB
            backupCount=5,
        )
        handler.name = 'ichrisbirch_file'
        handler.setLevel(getattr(logging, LOG_LEVEL))
        # Formatter is set in configure_structlog() to use structlog's renderer
        return handler
    except (OSError, PermissionError):
        return None


def configure_structlog():
    """Configure structlog - stdout always, file optionally."""
    # Shared processors for both stdlib and structlog
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

    # Check if file logging is enabled
    file_handler = _setup_file_handler()

    if file_handler:
        # Use stdlib logging backend to support both stdout and file
        logging.basicConfig(
            format='%(message)s',
            level=getattr(logging, LOG_LEVEL),
            stream=sys.stdout,
            force=True,
        )
        logging.root.addHandler(file_handler)

        # For stdlib, we need to render to string then pass to stdlib
        structlog.configure(
            processors=shared_processors
            + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure formatters for stdlib handlers
        if LOG_FORMAT == 'json':
            console_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
            file_formatter = console_formatter  # JSON is already plain text
        else:
            console_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(
                    colors=_use_colors(),
                    pad_level=True,
                ),
            )
            # File handler gets plain text (no colors)
            file_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(
                    colors=False,
                    pad_level=True,
                ),
            )

        for handler in logging.root.handlers:
            if handler.name == 'ichrisbirch_file':
                handler.setFormatter(file_formatter)
            else:
                handler.setFormatter(console_formatter)
    else:
        # No file logging - use simpler PrintLoggerFactory
        processors = shared_processors.copy()
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
