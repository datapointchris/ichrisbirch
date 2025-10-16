"""Utility functions for testing."""

import logging
import re

import httpx
from fastapi import status
from sqlalchemy.sql import select

from ichrisbirch.database.session import create_session

logger = logging.getLogger(__name__)
logger.info('testing util loaded')


def log_all_table_items(table_name, model, model_attribute=None):
    with create_session() as session:
        all_table_items = session.execute(select(model)).scalars().all()
        items = [getattr(item, model_attribute) if model_attribute else item for item in all_table_items]
        logger.warning(f'ALL {table_name.upper()}: {", ".join(items)}')


def show_status_and_response(response: httpx.Response) -> dict[str, str]:
    """Convert status code to description and return response if any."""
    d = {}
    try:
        for attr in dir(status):
            code = attr.split('_')[1]
            d[int(code)] = attr
    except ValueError:
        logger.warning('Failed to convert status code to description')
        d = {response.status_code: 'UNKNOWN'}
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError) as e:
        logger.warning(f'error decoding response content: {e}')
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}


def verify_page_title(response, title):
    """Check that the title is present in the response text."""
    # Match <title>, any whitespace/newlines, the title, and </title>
    found_title = None
    pattern = rf'<title>\s*{re.escape(title)}\s*</title>'
    if match := re.search(pattern, response.text):
        found_title = match.group(0).removeprefix('<title>').removesuffix('</title>').strip()
    assert title == found_title, f'expected title: {title}, found: {found_title}'
