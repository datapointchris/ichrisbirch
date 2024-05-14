import logging

import httpx
from flask import abort
from flask import flash


def url_builder(base_url: str, *parts) -> str:
    """Build a URL from a base URL and parts, will always include the trailing slash.

    Examples::
        >>> url_builder('http://example.com', 'api', 'v1', 'tasks')
        'http://example.com/api/v1/tasks/'

        >>> url_builder('http://example.com', 'api', 'v1', 'tasks', 1)
        'http://example.com/api/v1/tasks/1/'

        >>> API_URL = 'http://example.com/api/v1'
        >>> url_builder(API_URL, 'tasks')
        'http://example.com/api/v1/tasks/'
    """
    stripped_parts = []
    for part in parts:
        if isinstance(part, (list, tuple, set)):
            stripped_parts.extend([str(p).strip('/') for p in part if str(p).strip('/')])
        elif isinstance(part, str) and part.strip('/'):
            stripped_parts.append(part.strip('/'))
        elif isinstance(part, int):
            stripped_parts.append(str(part))
    return '/'.join([base_url.rstrip('/')] + stripped_parts) + '/'


def handle_if_not_response_code(response_code: int, response: httpx.Response, logger: logging.Logger):
    """Flash and log an error if the response status code is not the expected response code.

    Logger needs to be passed in as a parameter, or all logging is logged from the helpers file
    """
    if response.status_code != response_code:
        error_message = f'expected {response_code} from {response.url} but received {response.status_code}'
        logger.error(error_message)
        logger.error(response.text)
        flash(error_message, 'error')
        flash(response.text, 'error')
        abort(502, (f'{error_message}\n{response.text}'))


def convert_bytes(num: int | float) -> str:
    """Convert bytes to human readable format."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB'):
        if num < 1024.0 or unit == 'PB':
            break
        num /= 1024.0
    return f'{num:.2f} {unit}'
