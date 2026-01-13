"""Structlog configuration for the entire project.

Loggers are set up for: app, api, scheduler, and third-party libraries.
File logging is enabled when LOG_FILE_PATH environment variable is set.
GitHub Actions environment skips file logging (files don't exist in CI).

Note: 304 redirect filtering is handled by app.middleware.RequestLoggingMiddleware,
not by the logging configuration.
"""

import functools
import logging
import logging.handlers
import os
import sys

import structlog
from structlog.processors import CallsiteParameter
from structlog.processors import CallsiteParameterAdder

LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'


def configure_structlog():
    """Configure structlog with appropriate processors.

    In testing mode, uses stdlib logging to integrate with pytest's caplog.
    When LOG_FILE_PATH is set (and not in GitHub Actions), also logs to a rotating file.
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

    # Determine if we should use file logging
    use_file_logging = LOG_FILE_PATH and not GITHUB_ACTIONS

    if ENVIRONMENT == 'testing' or use_file_logging:
        # Use stdlib logging for pytest caplog integration and/or file logging
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

        # Create formatters based on LOG_FORMAT
        if LOG_FORMAT == 'json':
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        else:
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(
                    colors=sys.stdout.isatty() and ENVIRONMENT != 'testing',
                    pad_level=True,
                ),
            )

        # Configure stdlib root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler with rotation (if configured and not in GitHub Actions)
        if use_file_logging:
            file_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
                if LOG_FORMAT == 'json'
                else structlog.dev.ConsoleRenderer(colors=False, pad_level=True),
            )
            file_handler = logging.handlers.RotatingFileHandler(
                filename=LOG_FILE_PATH,
                maxBytes=10_000_000,  # 10 MB
                backupCount=3,
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    else:
        # Use PrintLoggerFactory for non-test environments without file logging
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
    """Suppress noisy third-party loggers and configure test loggers."""
    # Third-party loggers to quiet down when debug is on
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

    # Set tests.conftest to INFO to reduce noise during test runs
    logging.getLogger('tests.conftest').setLevel(logging.INFO)


@functools.lru_cache(maxsize=1)
def initialize_logging():
    """Initialize logging for the application."""
    configure_stdlib_logging()
    configure_structlog()
    logger = structlog.get_logger()
    logger.info('logging_initialized')
    return logger
