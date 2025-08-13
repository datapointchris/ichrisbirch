"""Assertion utilities for testing.

This module provides helper functions for common test assertions.
"""

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def show_status_and_response(response: httpx.Response) -> dict[str, Any]:
    """Format status code with description and response content for debugging.

    Args:
        response: The HTTP response to format

    Returns:
        Dictionary with status description as key and response content as value
    """
    from fastapi import status

    # Map status codes to descriptions
    status_dict = {}
    for attr in dir(status):
        if attr.startswith('HTTP_') and isinstance(getattr(status, attr), int):
            code = getattr(status, attr)
            status_dict[code] = attr

    # Extract content safely
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError) as e:
        logger.warning(f'Error decoding response content: {e}')
        content = '<no response content>'

    # Status code with description as key, content as value
    status_desc = status_dict.get(response.status_code, 'UNKNOWN')
    return {status_desc: content}


def verify_page_title(response, expected_title):
    """Check that the expected title is present in the response text.

    Args:
        response: The HTTP response to check
        expected_title: The title text that should be in the HTML title tags

    Raises:
        AssertionError: If the expected title is not found
    """
    # Match <title>, any whitespace/newlines, the title, and </title>
    found_title = None
    pattern = rf'<title>\s*{re.escape(expected_title)}\s*</title>'

    if match := re.search(pattern, response.text):
        found_title = match.group(0).removeprefix('<title>').removesuffix('</title>').strip()

    assert expected_title == found_title, f'Expected title: {expected_title}, found: {found_title}'
