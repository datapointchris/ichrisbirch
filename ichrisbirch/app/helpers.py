import logging

import httpx
from flask import abort, flash


def url_builder(base_url: str, *parts) -> str:
    """Build a URL from a base URL and parts, will always include the trailing slash"""
    stripped_parts = []
    for part in parts:
        if isinstance(part, (list, tuple, set)):
            stripped_parts.extend([str(p).strip('/') for p in part])
        elif isinstance(part, str):
            stripped_parts.append(part.strip('/'))
        elif isinstance(part, int):
            stripped_parts.append(str(part))
    return '/'.join([base_url.rstrip('/')] + stripped_parts) + '/'


def handle_if_not_response_code(response_code: int, response: httpx.Response, logger: logging.Logger):
    '''Flash and log an error if the response status code is not the expected response code.

    Logger needs to be passed in as a parameter, or all logging is logged from the helpers file
    '''
    if response.status_code != response_code:
        error_message = f'expected {response_code} from {response.url} but received {response.status_code}'
        logger.error(error_message)
        flash(error_message, 'error')
        abort(502, error_message)
