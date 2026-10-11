import functools
import inspect
import logging
import re
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

import structlog

logger = structlog.get_logger()

# Tracking query parameters to strip from URLs
TRACKING_PARAMS = frozenset(
    {
        # Google Analytics / UTM
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_content',
        'utm_term',
        'utm_id',
        # Platform click IDs
        'fbclid',
        'gclid',
        'gclsrc',
        'msclkid',
        'twclid',
        'igshid',
        'dclid',
        'wbraid',
        'gbraid',
        # Email / newsletter
        'mc_cid',
        'mc_eid',
        'ck_subscriber_id',
        'vero_id',
        # Substack / generic
        'publication_id',
        'post_id',
        'isfreemail',
        'triedredirect',
        # Common referral
        'ref',
        'referer',
        'referrer',
        'source',
        'medium',
        'campaign',
        # Misc
        'r',
        's',
        'st',
    }
)


def clean_url(url: str) -> str:
    """Strip tracking query parameters from a URL.

    Preserves non-tracking params (e.g. ?page=2, ?q=search).
    Returns the URL without a trailing '?' if all params were removed.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
    # urlencode with doseq=True to handle multi-value params
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query, fragment=''))


def find_project_root(
    directory: Path | None = None,
    target_file: str = 'pyproject.toml',
) -> Path:
    """Find the project root directory based on `target_file`"""
    if directory is None:
        directory = Path.cwd()
    for file in directory.iterdir():
        if file.name == target_file:
            return directory.absolute()
    parent_directory = directory.parent
    if parent_directory == directory:
        raise FileNotFoundError(f'Could not find project root directory searching for {target_file}')
    return find_project_root(parent_directory, target_file)


def get_logger_filename_from_handlername(handler_name: str) -> str | None:
    if (handler := logging.getHandlerByName(handler_name)) and isinstance(handler, logging.FileHandler):
        return Path(handler.baseFilename).name
    return None


SLUG_NON_ALNUM = re.compile(r'[^a-z0-9]+')


def slugify(text: str) -> str:
    """Lowercase, hyphenate, and strip a string into a URL-safe slug.

    "3:1 Vinaigrette Ratio" -> "3-1-vinaigrette-ratio"
    """
    lowered = text.lower().strip()
    hyphenated = SLUG_NON_ALNUM.sub('-', lowered)
    return hyphenated.strip('-')


def convert_bytes(num: int | float) -> str:
    """Convert bytes to human readable format."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB'):
        if num < 1024.0 or unit == 'PB':
            break
        num /= 1024.0
    return f'{num:.2f} {unit}'


def log_caller(func):
    @functools.wraps(func)
    def log_calling_function(*args, **kwargs):
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        caller_name = caller_frame.f_code.co_name
        caller_file = caller_frame.f_code.co_filename
        truncated_file = '/'.join(caller_file.split('/')[5:])
        logger.info('function_called', function=func.__name__, caller=caller_name, file=truncated_file)
        return func(*args, **kwargs)

    return log_calling_function
